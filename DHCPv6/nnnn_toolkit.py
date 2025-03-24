#!/usr/bin/python3

##########################################################################
#  _  _   _   _   ___ _____    ____        _       _   _                 
# | || | | \ | | |_ _|_   _|  / ___|  ___ | |_   _| |_(_) ___  _ __  ___ 
# | || |_|  \| |  | |  | |____\___ \ / _ \| | | | | __| |/ _ \| '_ \/ __|
# |__   _| |\  |  | |  | |_____|__) | (_) | | |_| | |_| | (_) | | | \__ \
#    |_| |_| \_| |___| |_|    |____/ \___/|_|\__,_|\__|_|\___/|_| |_|___/
#
##########################################################################
#
# Name:         nnnn_toolkit.py
# Company:      4N IT-Solutions GmbH
# Author:       Thomas Erhardt
# Date:         12.01.2022
#
# Description:  4N's Python toolkit with various useful functions
#
# Requirements: The following non-default Python modules are required:
#               nnnn_stackoverflow
#
# Known issues: -
#
# Tested with:  VitalQIP 20 on CentOS 8.4.2105
# 
# 
# Changelog:    
#  Date:        12.01.2022
#  Author:      Thomas Erhardt
#  Version:     1.0
#  Description: Initial Version
# 
#  Date:        19.08.2024
#  Author:      Julian Diehlmann
#  Version:     1.0
#  Description: Start adding support for QIP DHCPv6
##########################################################################

# dependencies : will be checked by installation script
# DEPENDS_ON_MODULE: fcntl,python3-libs
# DEPENDS_ON_MODULE: json,python3-libs
# DEPENDS_ON_MODULE: psutil,python3-psutil

# python doc
"""
4N's Python toolkit with various useful functions.
"""

# required modules
import os
import subprocess
from datetime import datetime
import re
import shutil
import logging
from logging.handlers import RotatingFileHandler
from logging.handlers import SysLogHandler
import json
import psutil
import configparser
import sys
import nnnn_stackoverflow as stackoverflow
import time
from threading import Timer

try:
   import fcntl
except ModuleNotFoundError:
   if os.name == 'posix':
      raise
##
## Initialize default logging including a custom log level TRACE
##
logger = logging.getLogger("CommonLogger")
logger.setLevel(logging.INFO)

# new custom logging level even more verbose than debug
numeric_level = getattr(logging, 'TRACE', None)
if not numeric_level:
   stackoverflow.addLoggingLevel('TRACE', logging.DEBUG - 5)

##
## generic stuff
##

def run_command(command,*command_args,password=None,timeout=None):
   """
   Run a command on OS level and capture exit code, STDOUT and STDERR.

   Parameters
   ----------
   command : str
      Can either be just a command name or the full command line
   command_args : list of str, optional
      Can either be a single list/array or tuple or individual arguments or a combination of all of these.
      Note: if command_args are specified command MUST only be the plain command name and cannot have
      additional arguments.
   password : str, optional
      If set the placeholder %PASSWORD% will be replaced after the command to be run has been logged,
      as a result the actual password will not be logged.
   timeout : int, optional
      The number of seconds to wait for the command to complete before considering it as a
      command that hangs.

   Returns
   -------
   error : int
      The exit code of the executed command.
   stdout : str
      The STDOUT of the executed command.
   stderr : str
      The STDERR of the executed command.

   Examples
   --------
   from nnnn_toolkit import run_command
   # all parameters specified as part of the command
   command_one = "ls -l"
   (error, stdout, stderr) = run_command(command_one)
   # parameters as list
   command_two = "ls"
   command_two_args = [ "-l", "-R", "/var/tmp" ]
   (error, stdout, stderr) = run_command(command_one, command_two_args)
   # avoid logging of password 
   command_three = "qip-getorganization -u user -p %PASSWORD%"
   password_three = "t0p.s3cret"
   (error, stdout, stderr) = run_command(command_three, password=password_three)
   """

   pw_placeholder = "%PASSWORD%"
   command_line = [ command ]
   use_shell = True
   for arg in command_args:
      use_shell = False
      if isinstance(arg,list) or isinstance(arg,tuple):
         for el in arg:
            command_line.append(el)
      else:
         command_line.append(arg)
   logger.debug("run_command : Running {}".format(command_line))
   if password:
      for i in range(len(command_line)):
         if command_line[i] == pw_placeholder:
            command_line[i] = password
         else:
            command_line[i] = re.sub(pw_placeholder, password, command_line[i])

   try:
      process = subprocess.Popen(command_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=use_shell)
   except PermissionError as e:
      return(99, "", "{}".format(e))

   if timeout:
      timer = Timer(timeout, process.kill)
      timer.start()
   try:
      stdout, stderr = process.communicate()
   finally:
      if timeout:
         timer.cancel()
   error = process.poll()
   if (error == -9):
      stderr = "Command timeout {} was reached and command was killed".format(timeout)
   logger.debug("run_command : Command completed with error code {}".format(error))
   return (error, stdout, stderr)

def scp(local_path, remote_server, remote_path, remote_user=None, ssh_port=None):
   """
   Use scp command to transfer a local file or directory to a remote server.

   It is assumed that SSH keys are properly set up so SSH does not require a password.

   Parameters
   ----------
   local_path - str
      The file or directory to be copied to the `remote_server`. Directories will
      be copied recursively.
   remote_server - str
      Hostname or IP address of the remote server.
   remote_path - str
      The file or directory name to copy the files or directories to on the `remote_server`.
   remote_user - str, optional
      SSH username to connect to the remote server.
   ssh_port - int, optional
      Alternate SSH port to use when connecting to the remote server

   Raises
   ------
   OSError
      If copying to remote server failed.
   """

   command = "scp"
   command_args = []

   # specific port?
   if ssh_port:
      command_args.extend([ "-P", "{}".format(ssh_port) ])

   # file or directory?
   if os.path.isdir(local_path):
      command_args.append("-r")
   command_args.append(local_path)

   # specific_user?
   if remote_user:
      command_args.append("{}@{}:{}".format(remote_user, remote_server, remote_path))
   else:
      command_args.append("{}:{}".format(remote_server, remote_path))

   # workaround for QIP env using libraries that break SSH/SCP commands
   # save & erase LD_LIBRARY_PATH value
   ld_library_path=os.getenv('LD_LIBRARY_PATH')
   os.putenv('LD_LIBRARY_PATH','')

   # run scp command in modified environment
   (error,stderr,stdout) = run_command(command, command_args)

   # restore LD_LIBRARY_PATH value
   os.putenv('LD_LIBRARY_PATH',ld_library_path)

   # done
   if error:
      raise OSError("scp failed with error code {}: {}".format(error,stdout))

def ssh(remote_command, remote_server, remote_user=None, ssh_port=None):
   """
   Excute a command on a remote server via SSH.

   It is assumed that SSH keys are properly set up so SSH does not required a password.

   Parameters
   ----------
   remote_command : str
      The command to execute on the remote host.
   remote_server - str
      Hostname or IP address of the remote server.
   remote_user - str, optional
      SSH username to connect to the remote server.
   ssh_port - int, optional
      Alternate SSH port to use when connecting to the remote server

   Raises
   ------
   OSError
      If executing the command via SSH fails.
   """

   command = "ssh"
   command_args = []

   # specific port?
   if ssh_port:
      command_args.extend([ "-P", "{}".format(ssh_port) ])

   # specific_user?
   if remote_user:
      command_args.append("{}@{}".format(remote_user, remote_server))
   else:
      command_args.append("{}".format(remote_server))

   # finally the remote command to execute
   command_args.append(remote_command)

   # workaround for QIP env using libraries that break SSH/SCP commands
   # save & erase LD_LIBRARY_PATH value
   ld_library_path=os.getenv('LD_LIBRARY_PATH')
   os.putenv('LD_LIBRARY_PATH','')

   # run scp command in modified environment
   (error,stderr,stdout) = run_command(command, command_args)

   # restore LD_LIBRARY_PATH value
   os.putenv('LD_LIBRARY_PATH',ld_library_path)

   # done
   if error:
      raise OSError("scp failed with error code {}: {}".format(error,stdout))


def backup_directory(source,target):
   """
   Backup complete directory (using tar).

   Parameters
   ----------
   source : str
      The (absolute) path of the directory to be backed up.
   target : str
      The (absolute) path of the directory where the backed up files will be placed. Must already exist.

   Returns
   -------
   int
      0 if success, > 0 on error
   """

   # check paths
   if not os.path.exists(source):
      logger.error("backup_directory : source directory '{}' does not exist".format(source))
      return 10
   if not os.path.exists(target):
      logger.error("backup_directory : target directory '{}' does not exist".format(target))
      return 20

   # run command to backup directory
   command = "cd {} || exit 1; tar cf - * | tar -C {} -xf -".format(source,target)
   (error, stdout, stderr) = run_command(command)
   if (error):
      logger.error("backup_directory : backing up files failed with error code {}: {}".format(error,stderr))
      return error

   return 0
   
def backup_daily(source,backup_base_dir=None):
   """
   Backup files into a directory using the name of the current weekday.
   Do nothing if daily backup directory is present and has been modified less than 24h ago.
   The target directory of the backup is the original directory with ".bak" appended to the path
   unless backup_base_dir is specified.

   Parameters
   ----------
   source : str
      The (absolute) path of the directory to back up.
   backup_base_dir : str, optional
      Path to the backup base directory where the numbered backup directories will be created.

   Returns
   -------
      0 on success or if nothing to do (see above), > 0 on error
   """

   if not backup_base_dir:
      backup_base_dir = "{0}.bak/daily".format(source)
   weekday = datetime.today().strftime("%A")
   backup_dir = "{0}/{1}".format(backup_base_dir,weekday)

   # create base dir if it does not exist yet 
   if not os.path.exists(backup_base_dir):
      try:
         os.makedirs(backup_base_dir,0o750)
      except Exception as error:
         logger.exception("backup_daily: Failed to create directory {0} : {1} - {2}".format(backup_base_dir,type(error).__name__,error))
         return 10

   # erase existing daily directory if older than a day 
   if os.path.exists(backup_dir):
      fstat = os.stat(backup_dir)
      now = datetime.now()
      last_mod = int(now.strftime('%s')) - int(fstat.st_mtime)
      logger.debug("backup_daily : {0} modified {1} seconds ago".format(backup_dir,last_mod))
      if (last_mod > 86000):
         logger.debug("backup_daily : Need to remove daily directory")
         try:
            shutil.rmtree(backup_dir)
         except Exception as error:
            logger.exception("backup_daily: Failed to delete directory {0} : {1} - {2}".format(backup_dir,type(error).__name__,error))
            return 20
      else:
         logger.debug("backup_daily : Daily backup already present, nothing to do")
         return 0

   # create daily backup dir and backup files
   try:
      os.mkdir(backup_dir,0o750)
   except Exception as error:
      logger.exception("backup_daily: Failed to create directory {0} : {1} - {2}".format(backup_dir,type(error).__name__,error))
      return 30
   error = backup_directory(source, backup_dir)
   if error:
      logger.error("backup_daily: Backing up files failed with error code {0}".format(error))
      return 40

   # done
   return 0

def backup_last_few(source,number_of_backups,backup_base_dir=None):
   """
   Backup files into a directory to keep the results of the given number of previous generations.

   By default the target directory of the backup is the original directory with ".bak/<number>" appended 
   to the path, unless `backup_base_dir` is specified.
   The backup with <number> = 1 is the most recent backup.

   Parameters
   ----------
   source : str
      Path to the directory to back up.
   number_of_backups : int
      Number of backups to keep.
   backup_base_dir : str, optional
      Path to the backup base directory where the numbered backup directories will be created.

   Returns
   -------
   int
      0 on success, > 0 if there is a failure.
   """

   if not backup_base_dir:
      backup_base_dir = "{}.bak/last_few".format(source)

   # create base dir if it does not exist yet 
   if not os.path.exists(backup_base_dir):
      try:
         os.makedirs(backup_base_dir,0o750)
      except Exception as error:
         logger.exception("backup_last_few: Failed to create directory {} : {} - {}".format(backup_base_dir,type(error).__name__,error))
         return 10

   # delete / rotate / create directories as required 
   for number in range(number_of_backups, 0, -1):
      backup_dir = backup_base_dir + "/" + str(number)
  
      # directory with the highest number needs to be removed
      if number == number_of_backups:
         if os.path.exists(backup_dir):
            try:
               shutil.rmtree(backup_dir)
            except Exception as error:
               logger.exception("backup_last_few: Failed to delete directory {} : {} - {}".format(backup_dir,type(error).__name__,error))
               return 20
      # directory with all but the last one need to be rotated
      else:
         if os.path.exists(backup_dir):
            rotate_backup_dir = backup_base_dir + "/" + str(number + 1)
            try:
               shutil.move(backup_dir, rotate_backup_dir)
            except Exception as error:
               logger.exception("backup_last_few: Failed to name directory {} to {1} : {} - {}".format(backup_dir,rotate_backup_dir,type(error).__name__,error))
               return 30

   # create new backup dir
   backup_dir = backup_base_dir + "/1"
   try:
      os.mkdir(backup_dir, 0o750)
   except Exception as error:
      logger.exception("backup_last_few: Failed to create directory {} : {} - {}".format(backup_dir,type(error).__name__,error))
      return 40

   # finally create backup
   error = backup_directory(source, backup_dir)
   if error:
      logger.error("backup_last_few: Backing up files failed with error code {}".format(error))
      return 50

   # done
   return 0

def copy_files(file_list, target_dir):
   """
   Backup a list of files to a specified directory. Uses "cp -a" command.

   Parameters
   ----------
   file_list : list
      A list of file names (strings) that might include wildcards or other patterns
      evaluated by the shell.
   target_dir : str
      The target directory (must exist).

   Raises
   ------
   FileNotFoundError
      If specified target directory does not exist.
   OSError
      If copying files fails.
   """

   # basic check
   if not os.path.isdir(target_dir):
      raise FileNotFoundError("Specified target directory {} does not exist".format(target_dir))

   # build copy command and execute it
   command = "cp"
   command_args = [ "-a" ]
   for file_pattern in file_list:
      command_args.append(file_pattern)
   command_args.append(target_dir)
   (error,stdout,stderr) = run_command(command, command_args)
   if error:
      raise OSError("Copying files using '{} {}' failed with error code {} : {}".format(command, command_args, error, stderr))

def save_logs(file_pattern, log_dir, tag = None):
   """
   Backup the files in `log_dir` that match the specified `file_pattern`.

   Logs will be backed up to a sub-directory within the `log_dir` by the
   name of save[.<tag>].YYYYmmdd where `tag` will only be used if specified.

   Parameters
   ----------
   file_pattern : str
      File name pattern (regex) for files that need to be copied.
   log_dir : str
      Path that contains the logs.
   tag : str, optional
      Will be used as part of the sub-directory that will be created

   Raises
   ------
   OSError
      In case directory cannot be created, log_dir does not exist
      or there is a permission problem.
   """

   # basic check
   if not os.path.isdir(log_dir):
      raise FileNotFoundError("Specified log directory {} does not exist".format(log_dir))

   # get list of files to copy
   file_list = []
   for file_name in os.listdir(log_dir):
      if re.match(file_pattern, file_name):
         file_path = os.path.join(log_dir,file_name)
         if os.path.isfile(file_path):
            file_list.append(file_path)

   # create sub dir
   time_format = "%Y%m%d.%H%M%S"
   now = time.localtime()
   timestamp = time.strftime(time_format, now)
   sub_dir = "save."
   if tag:
      sub_dir += tag + "."
   sub_dir += timestamp
   target_dir = os.path.join(log_dir,sub_dir)
   os.mkdir(target_dir, mode = 0o750)

   # copy files
   copy_files(file_list, target_dir)

def read_config(config_file, existing_config=None):
   """
   Read/Parse a JSON based configuration file and return as dict & JSON content.

   Parameters
   ----------
   config_file : str
      The (absolute) path to a configuration file in JSON syntax.
   existing_config : dict, optional
      An existing configuration that has been previously read which will be extended /
      overwritten by the newly read configuration file.

   Returns
   -------
   config : dict
      A dictionary representation of the configuration file contents.
   config_json : str
      The formatted (indented) JSON text from the configuration file.

   Raises
   ------
   OSError 
      If failure while opening/reading config file
   json.JSONDecodeError
      If failure to parse the JSON data
   """

   # setup
   config_json = ""
   if not existing_config:
      old_config = {}
   else:
      old_config = existing_config.copy()

   # read configuration file
   try:
      with open(config_file) as fd_config:
         config_json_tmp = fd_config.read()
   except OSError as error:
      raise

   # remove comments & blank lines
   config_json = ""
   for line in config_json_tmp.split("\n"):
      if re.search('^#|^\s+#|^$', line):
         continue
      line = re.sub('#.*', '', line)
      config_json += line + "\n"
   
   # parse configuration file
   try:
      config = json.loads(config_json)
   except json.JSONDecodeError as error:
      raise

   # merge configurations
   for key in config:
      old_config[key] = config[key]
   config = old_config

   # format configuration for printing
   config_json = json.dumps(config, indent = 3)

   return (config, config_json)

def is_running(name_of_process):
   """
   Check if there is a process with the specified name

   Parameters
   ----------
   name_of_process : str
      Name of the process to check

   Returns
   -------
   boolean
      True if there is at least one process with the specified name, False if not

   Examples
   --------
   from nnnn_toolkit import is_running
   if is_running("named"): 
      print("named is running")
   """
   for process in psutil.process_iter():
      if process.name() == name_of_process:
         return True
   return False

def get_list_item(my_list, primary_key, value):
   """
   Get one item from a list of dict identified by `primary_key`'s `value`.

   If there are multiple items using the same value for the specified
   `primary_key` the first matching item will be returned.

   Parameters
   ----------
   my_list : list of dict
      A list of items from that you want to pick one.
   primary_key : str
      Name of the primary key to look up in the list items.
   value : str
      Value assigned to the primary key that must match.

   Returns
   -------
   item : dict
      The item where the `primary_key`'s value matches the specified `value`.
      Might be `None` if there is no match.

   Examples
   --------
   from nnnn_toolkit import get_list_item
   items = [
      { "id" : 1, "data" = "foo" },
      { "id" : 2, "data" = "bar" }
   ]
   item_no_one = get_list_item(items, "id", 1)

   """
   # see if there is a match
   for item in my_list:
      if item[primary_key] == value:
         return item
   # if not return None
   return None

def get_list_items(my_list, key, value):
   """
   Get a list of items from a list of dicts where the specified `keys`'s `value` matches.
   This allows to filter a list of dicts by a specific key's value.

   Parameters
   ----------
   my_list : list of dict
      A list of items from that you want to pick one.
   key : str
      Name of the key to look up in the list items.
   value : str
      Value assigned to the key that must match.

   Returns
   -------
   item_list : list of dict
      The items where the `primary_key`'s value matches the specified `value`.
      Might be `None` if there is no match.

   Examples
   --------
   from nnnn_toolkit import get_list_items
   persons = [
      { "first_name" : "Heinz", last_name : "Erhardt" },
      { "first_name" : "Thomas", last_name : "Erhardt" },
      { "first_name" : "Ludwig", last_name : "Erhard" }
   ]
   erhardts_with_dt = get_list_items(persons, "last_name", "Erhardt")

   """
   item_list = []
   # see if there is a match
   for item in my_list:
      if item[key] == value:
         item_list.append(item)
   # done
   return item_list

def diff_list(my_list, other_list, name="Item", primary_key=None, additional_keys=None, missing_only=False):
   """
   Check which element (optionally identified by a key) from one list exists
   in another list.

   The comparison is one way, i.e. items in `other_list` that are not in `my_list` will
   not be reported. See Examples below how to implement two-way comparison.

   Parameters
   ----------
   my_list : list
      The original list to compare.
   other_list : list
      The list to compare with.
   name : str, optional
      Name of the elements to be compared, this will be used to create
      the diff result.
   primary_key : str, optional
      If the two lists contain dictionaries compare if the specified
      keys' value's exists in the other list.
   *additonal_keys : tuple, optional
      Additional keys that are supposed to be compared if the primary
      key's value matched.
   missing_only - boolean
      If `diff_messages` contain all messages about differences or only
      the ones about missing items.

   Returns
   -------
   diff_messages - list of str
      A list of printable descriptions of the differences that have been found.
   diff_data - dict
      The result consists of the following key/value data:
         "same":
            List of items that is the same in `my_list` and `my_other_list`.
            If `primary_key` is specified the value of the `primary_key`'s
            value is added to the list.
            Empty when `missing_only` is `True`.
         "missing":
            A list of items that are in `my_list` and not in `other_list`.
            `primary_key` is handled as in "same".
         "diff":
            A list of differences between the two lists (dict). 
            Only used when `keys` have been specified. 
            Empty when `missing_only` is `True`.
            Attributes of items in the list are:
               `primary_key` - the primary key that has been checked.
               "diff" - they attribute that differs between two list items.
               "my_value" - the attribute value of the item from `my_list`.
               "other_value" - the attribute value of the item from `other_list`.

   Examples
   --------
   # two way comparison
   from nnnn_toolkit import diff_list
   list_one = [ 'a', 'b', 'c' ]
   list_two = [ 'a', 'c', 'e' ]
   (diff_one, data_one) = diff_list(list_one, list_two)
   (diff_two, data_two) = diff_list(list_two, list_one, missing_only=True)
   print("Diff result list_one vs. list_two:")
   for message in diff_one:
      print(">" + message)
   for message in diff_two:
      print("<" + message)

   # comparison by key
   from nnnn_toolkit import diff_list, to_json
   list_one = [
      { "id" : 123, "name" : "Heinz" },
      { "id" : 321, "name" : "Thomas" },
      { "id" : 456, "name" : "Anna" }
   ]
   list_two = [
      { "id" : 123, "name" : "Heinz" },
      { "id" : 321, "name" : "Ludwig" }
   ]
   (diff, data) = diff_list(list_one, list_two, primary_key="id", additional_keys=[ "name" ])
   print(to_json(data))
   """

   # setup
   diff_messages = []

   same = []
   missing = []
   diff = []

   # handle additional keys
   keys = []
   if additional_keys:
      for item in additional_keys:
         if isinstance(item,list) or isinstance(item,tuple):
            for key in item:
               keys.append(key)
         else:
            keys.append(item)

   logger.trace("diff_list: Comparing '{}', primary_key '{}', additional_keys '{}', missing_only {}".format(name, primary_key, keys, missing_only))

   # iterate through lists
   for my_item in my_list:
      # standard list comparison
      if not primary_key:
         if my_item in other_list:
            if not missing_only:
               same.append(my_item)
         else:
            missing.append(my_item)
      # keys' value comparison
      else:
         found = False
         for other_item in other_list:
            # compare primary key first
            if my_item[primary_key] == other_item[primary_key]:
               logger.trace("diff_list: primary key value '{}' matched : {}".format(primary_key, my_item[primary_key]))
               found = True
               different = False
               # compare additional keys if required
               if not missing_only:
                  for key in keys:
                     logger.trace("diff_list: checking additional key '{}'".format(key))
                     # allow to compare optional additional keys which might not exist
                     if key not in my_item:
                        if key in other_item:
                           different = True
                           diff.append({ primary_key : my_item[primary_key], "diff" : key, "my_value" : "Not set", "other_value" : other_item[key] })
                     elif key not in other_item:
                        different = True
                        diff.append({ primary_key : my_item[primary_key], "diff" : key, "my_value" : my_item[key], "other_value" : "Not set" })
                     elif my_item[key] != other_item[key]:
                        different = True
                        diff.append({ primary_key : my_item[primary_key], "diff" : key, "my_value" : my_item[key], "other_value" : other_item[key] })
               # no difference
               if not different:
                  if not missing_only:
                     same.append(my_item[primary_key])
               # done with this my_item
               break
         # missing
         if not found:
            missing.append(my_item[primary_key])

   # create diff messages
   for missing_item in missing:
      diff_messages.append("{} missing: '{}'".format(name,missing_item))
   if not missing_only:
      for value in diff:
         diff_messages.append("{} '{}' {} is different: '{}' vs. '{}'".format(name,value[primary_key],value["diff"],value["my_value"],value["other_value"]))

   # create diff_data
   diff_data = {}
   diff_data["same"] = same
   diff_data["missing"] = missing
   diff_data["diff"] = diff

   # done
   return (diff_messages, diff_data)

def to_json(data):
   """
   Convert `data` to a printable (formatted) JSON string

   Parameters
   ----------
   data - dict
      The structured data to convert to JSON.

   Returns
   -------
   json_data - str
      The formatted JSON data.
   """
   return json.dumps(data, indent = 3)

def read_qip_pcy(pcy_file):
   """
   Read qip.pcy file and return as dict.

   Note: might raise additional exceptions (any exception that might be raised by configparser)

   Parameters
   ----------
   pcy_file : str
      The (absolute) path to the qip.pcy

   Returns
   -------
   config : dict
      A dictionary representation of the configuration file contents
   config_json : str
      The formatted (indented) JSON text representation of the configuration file

   Raises
   ------
   FileNotFoundError
      If specified file does not exist
   OSError
      If failure while opening/reading config file
   """
   
   # make sure specified file exists
   if not os.path.exists(pcy_file):
      raise FileNotFoundError("No such file {}".format(pcy_file))

   # use ConfigParser that supports multiple options
   config_parser = stackoverflow.ConfigParserMultiOpt()
   config_parser.read(pcy_file)
   config = {}
   config["DEFAULT"] = config_parser.defaults()
   for section in config_parser.sections():
      config[section] = {}
      for key in config_parser[section]:
         config[section][key] = config_parser[section][key]
   config_json = json.dumps(config, indent = 3)
   return (config, config_json)


##
## class Logger
##
class Logger:
   """
   Reduces the complexity of the logging module.
   """
   
   def __init__(self, log_file = None, console_logging = False, syslog_logging = False, overwrite = False):
      """
      Initialize logger with name "CommonLogger".
      Set up formatting using logging.Formatter.
      Set up file logging using logging.FileHandler (if required) and/or setup console logging using logging.StreamHandler (if required).
      Set default logging level (INFO) and add a custom logging level (TRACE)

      Parameters
      ----------
      log_file : str, optional
         The (absolute) path to the logfile to that logging messages should be written. By default (see `overwrite`) log messages
         will be appended. Either `log_file` or `console_logging = True` must be specified.
      console_logging : boolean, optional
         Enable logging to the console / STDOUT. Either `log_file` or `console_logging = True` must be specified.
      syslog_logging : boolean, optional
         Enable logging to local system. 
         Only messages up to info are logged to syslog, no matter if the logging level is set to a more verbose value,
         by default only messages up to warning are logged to syslog. Use `set_syslog_level` to change the logging level.
         Will use /dev/log to log to syslog with facilitcy 'user'
      overwrite : boolean, optional
         If True overwrite the given logfile instead of appending to it.

      Examples
      --------

      # log to file, no overwrite
      import nnnn_toolkit as toolkit
      logger = toolkit.logger("/my/log/file")
      logger.info("logging to a file now")

      # log to console only
      import nnnn_toolkit as toolkit
      logger = toolkit.logger(console_logging=True)
      logger.info("logging to STDOUT")

      # log to file with overwrite, log to console, too
      import nnnn_toolkit as toolkit
      logger = toolkit.logger(
      """

      # either file logging or console logging needs to be enabled
      if not log_file and not console_logging and not syslog_logging:
         raise AttributeError("At least one of 'log_file' or 'console_logging' or 'syslog_logging' must be specified")

      self.__logger_name = "CommonLogger"

      self.__log_formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
      self.__syslog_formatter = logging.Formatter("{}: %(message)s".format(sys.argv[0]))
      self.__log_file = log_file
      self.__console_logging = console_logging
      self.__syslog_logging = syslog_logging

      # create logger
      self.__logger = logging.getLogger(self.__logger_name)
      self.__logger.setLevel(logging.INFO)
      self.__logger.propagate = False

      # file handler (if required)
      if self.__log_file:
         if overwrite:
            self.__log_filehandler = logging.FileHandler(log_file, mode='w')
         else:
            self.__log_filehandler = logging.FileHandler(log_file, mode='a')
         self.__log_filehandler.setLevel(logging.INFO)
         self.__log_filehandler.setFormatter(self.__log_formatter)
         self.__logger.addHandler(self.__log_filehandler)

      # console handler (if required)
      if self.__console_logging:
         self.__console_handler = logging.StreamHandler()
         self.__console_handler.setLevel(logging.INFO)
         self.__console_handler.setFormatter(self.__log_formatter)
         self.__logger.addHandler(self.__console_handler)

      # syslog hanlder (if required)
      if self.__syslog_logging:
         self.__syslog_handler = logging.handlers.SysLogHandler(address = '/dev/log')
         self.__syslog_handler.setLevel(logging.WARNING)
         self.__syslog_handler.setFormatter(self.__syslog_formatter)
         self.__logger.addHandler(self.__syslog_handler)
      
      # new custom logging level even more verbose than debug
      numeric_level = getattr(logging, 'TRACE', None)
      if not numeric_level:
         stackoverflow.addLoggingLevel('TRACE', logging.DEBUG - 5)

   def destroy(self):
      """
      Disable logging.
      """

      # remove all handlers
      if self.__log_file:
         self.__logger.removeHandler(self.__log_filehandler)
      if self.__console_logging:
         self.__logger.removeHandler(self.__console_handler)
      if self.__console_logging:
         self.__logger.removeHandler(self.__syslog_handler)

      # done
      return None
   
   def set_level(self, level):
      """
      Set logging level 
      
      Parameters
      ----------
      level : str
         one of CRITICAL, ERROR, WARNING, INFO, DEBUG, TRACE

      Returns
      -------
      int
         0 on success, > 0 on error
      """

      # validate specified logging level
      match = re.search('^(CRITICAL|ERROR|WARNING|INFO|DEBUG|TRACE)$', level)
      if not match:
         self.__logger.error("Invalid logging level {0}".format(level))
         return 10

      # set new level on logger itself and all handlers
      numeric_level = getattr(logging, level, None)
      self.__logger.setLevel(numeric_level)
      if self.__log_file:
         self.__log_filehandler.setLevel(numeric_level)
      if self.__console_logging:
         self.__console_handler.setLevel(numeric_level)

      # done
      return 0

   def set_syslog_level(self, level):
      """
      Set logging for syslog

      Parameters
      ----------
      level : str
         one of CRITICAL, ERROR, WARNING, INFO

      Returns
      -------
      int
         0 on success, > 0 on error
      """

      # validate specified logging level
      match = re.search('^(CRITICAL|ERROR|WARNING|INFO)$', level)
      if not match:
         self.__logger.error("Invalid syslog logging level {0}".format(level))
         return 10

      # set new level on logger itself and all handlers
      numeric_level = getattr(logging, level, None)
      self.__syslog_handler.setLevel(numeric_level)

      # done
      return 0
   
   def enable_rotate_logging(self, size, number_of_backups):
      """
      Enable log file rotation

      Parameters
      ----------
      size : str
         A number and optionally a unit which can be one of (B)ytes, (K)ilobytes, (M)egabytes, (G)igabytes.
         If no unit is specified bytes are assumed as the unit.
         Valid examples are : 1024, 10K, 10M, 1G
      number_of_backups : int
         Specifies the number of backups to keep in addition to the current logfile.
         Backups will be named <name-of-logfile>.<number> where number starts at 1.
      """

      # check if logging to file is enabled at all
      if not self.__log_file:
         self.__logger.error("No log file used, log rotation not allowed")
         return 10

      # check if given parameters are valid
      rotate_number_of_backups = number_of_backups
      match = re.search("^([0-9]+)([BKMG]{0,1})$", size)
      if not match:
         self.__logger.error("Invalid value '" + size + "' for 'log_rotate_file_size' in configuration file")
         return 20

      # calculate size in bytes as required for RotatingFileHandler
      value = match.group(1)
      unit = match.group(2)
      rotate_file_size = int(value)
      if unit == "K":
         rotate_file_size *= 1024
      if unit == "M":
         rotate_file_size *= 1024 * 1024
      if unit == "G":
         rotate_file_size *= 1024 * 1024 * 1024
      self.__logger.debug("Max log file size is " + str(value) + str(unit) + " (" + str(rotate_file_size) + " Bytes)")

      # set up log rotation
      if rotate_file_size > 0 and rotate_number_of_backups > 0:
         try:
            log_rotate_filehandler = RotatingFileHandler(self.__log_file, maxBytes=rotate_file_size, backupCount=rotate_number_of_backups)
         except Exception as error:
            self.__logger.exception("Cannot initialize rotated logging using logfile " + self.__log_file + ": {0} : {1}".format(type(error).__name__,error))
            return 30
         log_rotate_filehandler.setLevel(self.__logger.getEffectiveLevel())
         log_rotate_filehandler.setFormatter(self.__log_formatter)
         self.__logger.removeHandler(self.__log_filehandler)
         self.__log_filehandler.flush()
         self.__log_filehandler.close()
         self.__logger.addHandler(log_rotate_filehandler)
      else:
         self.__logger.error("enable_rotate_logging : size ({0}{1}) and number_of_backups ({2}) both need to be > 0".format(rotate_file_size, unit, rotate_number_of_backups))

   def trace(self, message):
      """
      Log message for level TRACE if current logger level is TRACE or lower

      Parameters
      ----------
      message : str
         The message to log
      """
      self.__logger.trace(message)

   def debug(self, message):
      """
      Log message for level DEBUG if current logger level is DEBUG or lower

      Parameters
      ----------
      message : str
         The message to log
      """
      self.__logger.debug(message)

   def info(self, message):
      """
      Log message for level INFO if current logger level is INFO or lower

      Parameters
      ----------
      message : str
         The message to log
      """
      self.__logger.info(message)

   def warn(self, message):
      """
      Log message for level WARN if current logger level is WARN or lower

      Parameters
      ----------
      message : str
         The message to log
      """
      self.__logger.warn(message)

   def warning(self, message):
      """
      Log message for level WARN if current logger level is WARN or lower

      Parameters
      ----------
      message : str
         The message to log
      """
      self.__logger.warning(message)

   def error(self, message):
      """
      Log message for level ERROR if current logger level is ERROR or lower

      Parameters
      ----------
      message : str
         The message to log
      """
      self.__logger.error(message)

   def exception(self, message):
      """
      Log message for level ERROR if current logger level is ERROR or lower.
      Use if an expection has been caught that won't be raised.

      Parameters
      ----------
      message : str
         The message to log
      """
      self.__logger.exception(message)

   def critical(self, message):
      """
      Log message for level CRITICAL if current logger level is CRITICAL or lower.

      Parameters
      ----------
      message : str
         The message to log
      """
      self.__logger.critical(message)


class stopwatch():
   """
   Context Manager to print duration for a specific set of instructions / commands.
   Will print an informal message on start and stop, precision of printed duration is in
   seconds.

   Example
   -------

   from nnnn_toolkit import stopwatch

   logger = toolkit.Logger(console_logging = True)

   with stopwatch("Doing something"):
      # do something here
   """

   def __init__(self, message):
      """
      Parameters
      ----------
      message - str
         The message to print when starting and stopping a set of instructions.
      """
      self.message = message

   def __enter__(self):
      self.start_time = time.time()
      logger.info(self.message)

   def __exit__(self, exception_type, exception_value, exception_traceback):
      self.stop_time = time.time()
      duration = round(self.stop_time - self.start_time)
      logger.info("{} completed after {} seconds".format(self.message, duration))

class singleInstance():
   """
   Context Manager to ensure that only one instance of a certain script is running at a time.

   Will try to create lockfile to prevent another instance from running. 
   If an instance detects a lockfile and `max_runtime` is specified, the 
   new instance attempts to kill the already running instance of the script.

   Example
    -------

   use nnnn_toolkit as toolkit
   with toolkit.singleInstance(lock_file='/opt/qip/current/tmp/myscript.lock') as myscript:
      print("New instance started with pid", myscript.pid)
   """

   def __init__(self, lock_file=None, max_runtime=None):
      """
      Set up instance variables for later use.
   
      Parameters
      ----------
      lock_file : str, optional
         The path to the lock file used to signal to another instance of a script that 
         this instance of the script is already running.
      max_runtime : str, optional
         The maximum runtime allowed for another instance that is already running.
      """

      # determine lockfile name automatically if not specified
      if not lock_file:
         self.lock_file = os.path.abspath(sys.argv[0]) + ".lock"
      else:
         self.lock_file = lock_file
      # max runtime
      self.max_runtime = max_runtime
      # number of attempts to kill already running instance if max runtime is exceeded
      self.max_tries = 5
      # sleep time between multiple tries
      self.sleep_time = 3
      # pid of this instance
      self.pid = os.getpid()

   def __enter__(self):
      """
      Creates a file to be used as lockfile that will be exclusively locked.
      If the lockfile is actually logged check runtime of previously started instance.
      If runtime exceeds (optionally) specified maximum runtime, try to stop the other
      instance and then lock the file.
      """
      for my_try in range(1,self.max_tries + 1):
         try:
            # create lock file without overwriting it's content (if present)
            self.lock_file_fh = open(self.lock_file, "a+")
         except OSError as error:
            # issue with lock file
            logger.error("Cannot access lock file: {} - {}".format(type(error).__name__,error))
            exit(10)

         # attempt to lock the lock file
         if my_try > 1:
            logger.info("Re-trying to acquire lock (try #{})".format(my_try))
         try:
            # lock file exclusively, non-blocking
            fcntl.lockf(self.lock_file_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # successfully locked : write pid to lockfile
            self.lock_file_fh.seek(0)
            self.lock_file_fh.truncate()
            self.lock_file_fh.write(str(self.pid))
            self.lock_file_fh.flush()

            # done
            return self

         except BlockingIOError:
            # failed to lock
            self.lock_file_fh.seek(0)
            self.other_pid = self.lock_file_fh.read()
            if my_try <= 1:
               logger.info("Another instance is already running: {}".format(self.other_pid))
            else:
               logger.info("Another instance is still running: {}".format(self.other_pid))

            # check if other process should be killed
            if not self.max_runtime:
               exit(20)

            # determine how long other process has been running
            lockfile_stat = os.stat(self.lock_file)
            lockfile_create_time = lockfile_stat.st_ctime
            current_time = time.mktime(time.localtime())
            time_diff = current_time - lockfile_create_time

            if time_diff >= self.max_runtime:
               # running for too long : try to kill it
               logger.info("Other instance is running for more than {} seconds, stopping it (try #{})".format(self.max_runtime, my_try))
               try:
                  proc = psutil.Process(int(self.other_pid))
                  proc.terminate()
                  time.sleep(self.sleep_time)
                  # kill other process during try before last try
                  if my_try >= self.max_tries - 1:
                      logger.info("Other instance cannot be stopped, killing it".format(self.max_runtime, my_try))
                      proc.kill()
                      time.sleep(self.sleep_time)
               except Exception as error:
                  # this might happen if running instance is owned by a different user
                  logger.error("Unable to stop already running instance: {} - {}".format(type(error).__name__,error))
                  exit(30)
            else:
               # running less than max_runtime : OK
               logger.info("Other instance is running for less than {} seconds, exiting".format(self.max_runtime))
               exit()

      # failed to lock or failed to kill after max_tries
      logger.error("Other instance with pid {} is still running and cannot be stopped".format(self.other_pid))
      exit(40)

   def __exit__(self, exception_type, exception_value, exception_traceback):
      """
      Close lockfile and remove it.
      """
      # cleanup
      self.lock_file_fh.close()
      os.unlink(self.lock_file)

      # handle exception in with-block
      if exception_type:
         raise

##
## DNS specific
##

class NamedConf:
   """
   Provides easy access to (selected) named.conf contents.
   Note: Currently limited to the elements of the configuration that the 4N userexits require to work.
   """

   ### TODO: handle exclusions in ACLs

   def __init__(self, named_conf_dir, file_name="named.conf", change_dir=None):
      """
      Read and parse named.conf to be able to provide easy access to configuration elements or the whole configuration.
      Note that to make parsing easier named-checkconf -p is called first.
      See `get_config` for a description of how to access the elements of the configuration.

      Parameters
      ----------
      named_conf_dir : str
         The (absolute) path to the directory that contains the named.conf file to be read.
      file_name : str, optional
         The name of the named configuration file to be read, defaults to named.conf.
      change_dir: str, optional
         The directory to change to before checking named.conf (see named-checkconf -X).

      Raises
      ------
      SystemError
         In case normalizing the named.conf contents with named-checkconf -p fails.
      SyntaxError
         In case unsupported syntax is detected, e.g. zone's file with absolute path.
      """
   
      check_conf = 'named-checkconf'
      found = False
      bin_dirs = ('/opt/qip/current/usr/bin', '/opt/qip/usr/bin')
      for bin_dir in bin_dirs:
         check_conf_path = os.path.join(bin_dir,check_conf)
         if os.path.exists(check_conf_path):
            found = True
            break
      if not found:
            raise SystemError("NamedConf: cannot determine path to named-checkconf")
      named_conf_path = os.path.join(named_conf_dir,file_name)
      if not change_dir:
         change_dir=named_conf_dir

      # some variables that might be useful later on
      self.__named_conf_raw = ""
      self.__named_conf_dir = named_conf_dir
      self.__change_dir = change_dir
      self.__evaluated_acls = {}
      self.__acl_predefined = {}
      self.__zone_dynamic_status = {}
      self.__no_view_name = "__NO_VIEW__"
      self.__default_if_not_set = { "allow-transfer" : "any", "allow-query" : "any", "allow-update" : "none", "update-policy" : "", "notify" : "yes" }
   
      # normalize named.conf to make parsing easier
      command = check_conf_path
      command_args = ("-X", change_dir, "-p", named_conf_path)
      (error,stdout,stderr) = run_command(command, command_args)
      if (error):
         raise SystemError("NamedConf: normalizing named.conf failed with error code " + str(error) + ": " + stdout)
      self.__named_conf_raw = stdout

      # parse named.conf
      named_conf = {}
      line_cnt = 0
   
      view_name =  self.__no_view_name
      journal_file_dir = ""
   
      in_key = 0
      in_acl = 0
      in_view = 0
      in_zone = 0
      in_options = 0
      in_allow_list = 0
      in_primaries = 0
   
      counters = {}
      counters["views"] = 0
      counters["keys"] = 0
      counters["zones"] = 0
      counters["acls"] = 0
   
      lines = stdout.split("\n")
      for line in lines:
         line_cnt += 1
         #print("XXX " + str(line_cnt) + " - '" + line + "'")
         if line == "":
            continue

         # options
         match = re.search('^options {', line)
         if match:
            in_options = 1
            logger.trace("NamedConf : detected options at line " + str(line_cnt))
            if "options" not in named_conf:
               named_conf["options"] = []
         if in_options:
            # end of options block
            match = re.search('^};', line)
            if match:
               in_options = 0

         # views
         match = re.search('^view "(.*)" {', line)
         if match:
            in_view = 1
            view_name = match.group(1)
            logger.trace("NamedConf : detected view '" + view_name + "' at line " + str(line_cnt))
            if "views" not in named_conf:
               named_conf["views"] = []
            named_conf["views"].append({ "view_name" : view_name, "options" : [] })
            if "views" in counters:
               counters["views"] += 1
            else:
               counters["views"] = 1
         if in_view:
            # end of view block
            match = re.search('^};', line)
            if match:
               in_view = 0
   
         # key
         match = re.search('^key "(.*)" {', line)
         if match:
            in_key = 1
            key_name = match.group(1)
            logger.trace("NamedConf : detected key '" + key_name + "' at line " + str(line_cnt))
            if "keys" not in named_conf:
               named_conf["keys"] = []
            named_conf["keys"].append({ "key_name" : key_name })
            if "keys" in counters:
               counters["keys"] += 1
            else:
               counters["keys"] = 1
         if in_key:
            # key properties
            match = re.search('^\s+algorithm "(.*)";', line)
            if match:
               key_algorithm = match.group(1)
               key = named_conf["keys"][-1]
               key["algorithm"] = key_algorithm
            match = re.search('^\s+secret\s+"(.*)";', line)
            if match:
               key_secret = match.group(1)
               key = named_conf["keys"][-1]
               key["secret"] = key_secret
               in_key = 0
   
         # ACL
         match = re.search('^acl "(.*)" {', line)
         if match:
            in_acl = 1
            acl_name = match.group(1)
            logger.trace("NamedConf : detected ACL '" + acl_name + "' at line " + str(line_cnt))
            if "acls" not in named_conf:
               named_conf["acls"] = []
            named_conf["acls"].append({ "acl_name" : acl_name })
            if "acls" in counters:
               counters["acls"] += 1
            else:
               counters["acls"] = 1
         if in_acl:
            # ACL members
            match = re.search('^\s+(\S+);', line)
            if match:
               acl_member = match.group(1)
               acl = named_conf["acls"][-1]
               if "members" not in acl:
                  acl["members"] = []
               acl["members"].append(acl_member)
            # end of ACL block
            match = re.search('^};', line)
            if match:
               in_acl = 0
   
         # start of zone block
         match = re.search('^(\s*)zone "(.*)" .*{', line)
         if match:
            in_zone = 1
            zone_indent = match.group(1)
            zone_name = match.group(2)
            logger.trace("NamedConf : detected zone '" + zone_name + "' at line " + str(line_cnt))
            if "zones" in counters:
               counters["zones"] += 1
            else:
               counters["zones"] = 1
         if in_zone:
            # zone properties
            # zone type
            match = re.search('^\s+type\s+([a-z]+);', line)
            if match:
               zone_type = match.group(1)
               # append zone to configuration
               if "views" not in named_conf:
                  named_conf["views"] = []
                  named_conf["views"].append({ "view_name" : view_name })
               view = named_conf["views"][-1]
               if "zones" not in view:
                  view["zones"] = []
               view["zones"].append({ "zone_name" : zone_name, "zone_type" : zone_type, "zone_file" : None, "zone_file_path" : None, "has_journal" : False, "journal_file_path" : None, "options" : [] })
            # zone file / journal file default
            match = re.search('^\s+file\s+"(.*)";', line)
            if match:
               zone_file = match.group(1)
               # absolute vs. relative path
               if re.search('^/', zone_file):
                  raise SyntaxError("Full qualified zone file names are not supported, affected zone is {}, zone file is configured as {}".format(zone_name,zone_file))
               zone_file_path = named_conf_dir + "/" + zone_file
               journal_file_path = journal_file_dir + "/" + zone_file + ".jnl"
               # check if journal exists
               has_journal = False
               if os.path.exists(journal_file_path):
                  logger.trace("NamedConf : zone '" + zone_name + "' has journal file")
                  has_journal = True
               zone = view["zones"][-1]
               zone["zone_file"] = zone_file
               zone["zone_file_path"] = zone_file_path
               zone["journal_file_path"] = journal_file_path
               zone["has_journal"] = has_journal
            # journal file specific
            match = re.search('^\s+journal\s+"(.*)";', line)
            if match:
               journal_file = match.goup(1)
               # absolute vs. relative path
               if re.match('^/', journal_file):
                  raise SyntaxError("Full qualified journal file names are not supported, affected zone is {}, journal file is configured as {}".format(zone_name,journal_file))
               journal_file_path = journal_file_dir + "/" + journal_file
               view = named_conf["views"][-1]
               zone = view["zones"][-1]
               zone["journal_file_path"] = journal_file_path
            # end of zone block
            pattern = '^' + zone_indent + '};'
            match = re.search(pattern, line)
            if match:
               in_zone = 0

         # options which consist of lists that can be global / per view / per zone
         if in_options or in_view or in_zone:
            match = re.search('^(\s+)(allow-[a-z]+|match-clients|update-policy|forwarders|masters|primaries|also-notify)\s+{$', line)
            if match:
               list_indent = match.group(1)
               list_name = match.group(2)
               in_allow_list = 1
               list_definition = { "option_name" : list_name }
               if in_zone:
                  view = named_conf["views"][-1]
                  zone = view["zones"][-1]
                  zone["options"].append( list_definition )
                  logger.trace("appending " + list_name + " to zone " + zone["zone_name"] + " at line " + str(line_cnt))
               elif in_view:
                  view = named_conf["views"][-1]
                  view["options"].append( list_definition )
                  logger.trace("appending " + list_name + " to view " + view["view_name"] + " at line " + str(line_cnt))
               if in_options:
                  named_conf["options"].append( list_definition )
                  logger.trace("appending " + list_name + " to global options at line " + str(line_cnt))
            if in_allow_list:
               # end of block
               pattern = '^' + list_indent + '};'
               match = re.search(pattern, line)
               if match:
                  in_allow_list = 0
               # entries in list (can be keys, address-lists, or grant/deny clauses of upate-policy)
               pattern = '^' + list_indent + '\s+(\S+|\S+\s+port\s+[0-9]+|key ".*"|grant.*|deny.*);$'
               match = re.search(pattern, line)
               if match:
                  list_member = match.group(1)
                  if in_zone:
                     view = named_conf["views"][-1]
                     zone = view["zones"][-1]
                     allow_list = zone["options"][-1]
                     logger.trace("appending list member " + list_member + " to zone " + zone["zone_name"] + " at line " + str(line_cnt))
                  elif in_view:
                     view = named_conf["views"][-1]
                     allow_list = view["options"][-1]
                     logger.trace("appending list member " + list_member + " to view " + view["view_name"] + " at line " + str(line_cnt))
                  if in_options:
                     allow_list = named_conf["options"][-1]
                     logger.trace("appending list member " + list_member + " to global options at line " + str(line_cnt))
                  if "members" not in allow_list:
                     allow_list["members"] = []
                  allow_list["members"].append(list_member)

         # options which have a single value that can be global / per view / per zone - or just one of those
         if in_options or in_view or in_zone:
            match = re.search('\s+(directory|notify|update-policy|hostname|version)\s+(\S+);$', line)
            if match:
               option_name = match.group(1)
               option_value = match.group(2)
               option_definition = { "option_name" : option_name, "option_value" : option_value }
               if in_zone:
                  view = named_conf["views"][-1]
                  zone = view["zones"][-1]
                  zone["options"].append(option_definition)
                  logger.trace("appending " + option_name + " to zone " + zone["zone_name"] + " at line " + str(line_cnt))
               elif in_view:
                  view = named_conf["views"][-1]
                  view["options"].append(option_definition)
                  logger.trace("appending " + option_name + " to view " + view["view_name"] + " at line " + str(line_cnt))
               if in_options:
                  named_conf["options"].append(option_definition)
                  logger.trace("appending " + option_name + " to global options at line " + str(line_cnt))
               # special handling of directory option - needed to determine journal file path
               if option_name == "directory":
                  journal_file_dir = option_value
                  # remove quotes
                  journal_file_dir = journal_file_dir.replace('"','')

      # update statistics & non-config settings
      named_conf["counters"] = counters
      if counters["views"] > 0:
         named_conf["has_views"] = True
      else:
         named_conf["has_views"] = False
  
      # save result for further use
      self.__named_conf = named_conf

   def get_config_raw(self):
      """
      Provide normalized named.conf text as created by named-checkconf -p

      Returns
      -------
      str
         The normalized named.conf contents
      """
      return self.__named_conf_raw

   def get_config(self):
      """
      Provide named.conf as dictionary representing the various elements of the configuration.
      Note that not all elements and options are supported.

      The elements present (if found in named.conf) are as follows:
         "acls" : List of ACLs. 
            Each ACL is a dict that consists of an "acl_name" and "members". "members" is a list of strings
            representing the address-list elements (in the sense of named.conf syntax) found in named.conf

         "options" : List of the global options. 
            Each option is a dict that consists of an "option_name" plus either an "option_value"
            or "members" if the option can contain a list of values.

         "views" : List of views. 
            Each view is a dict which consists if a "view_name", "options" (which is a list of options like the
            global options list) and "zones" which is in turn a list of zones.

            Each zone in the "zones" list is again a dictionary which has a "zone_name", "zone_type", "zone_file", "zone_file_path"
            and "options" (again like the global options).

            Note that if no views are defined a dummy view will be assumed which is called "__NO_VIEW__"

         "keys" : a list of keys. Each key has a "key_name", "algorithm" and "secret"

      In addition the following elements are added that are not part of named.conf:
         "counters" : a dictionary that contains information about how many views, keys, zones and acls have been found in the configuration.
         "has_views" : a boolean value that is True if at least one "view" statement has been found in named.conf
         For each zone also the following properties are added : "has_journal" and "journal_file_path"

      Options that are currently supported are: 
         "allow-*", "match-clients", "update-policy",
         "directory", "notify", "hostname", "version",
         "notify", "also-notify", 
         "forwarders", "masters", "primaries"

      Note that additional methods exist to provide direct access to the elements described above, e.g. `get_view` to get
      only that part of the configuration that represents one specific view.

      Returns
      -------
      dict
         The dictionary representation of the named.conf contents
      """
      return self.__named_conf

   def get_json(self):
      """
      Provide named.conf contents as JSON.

      Returns
      -------
      json_data : str
         Formatted (indented) JSON data representing the named.conf data.
      """
      # dump data as JSON for verification purposes
      json_data = json.dumps(self.__named_conf, indent = 3)
      return(json_data)

   def has_views(self):
      """
      Check if named.conf has at least one view definition.

      Returns
      -------
      boolean
         True if there is a least one view in named.conf, False otherwise.
      """
      return self.__named_conf["has_views"]

   def get_option_default(self, option_name):
      """
      Get the default value for an option if it's not set at all in the configuration.
      Currently only supported selected options.

      Parameters
      ----------
      option_name : str
         Name of the option for that the default value is needed.
         Supported options are: "allow-transfer", "allow-query", "allow-update", "update-policy", "notify"

      Returns
      -------
      str
         Default value for the specified `option_name`.

      Raises
      ------
      KeyError
         If the given `option_name` is not one of the supported options.
      """
      if option_name in self.__default_if_not_set:
         return self.__default_if_not_set[option_name]
      else:
         raise KeyError("NamedConf.get_option_default : default value for option " + option_name + " unknown")

   def evaluate_acl(self, name_of_acl):
      """
      Recursively evaluate all references to other ACLs within the given ACL.

      Parameters
      ----------
      name_of_acl : str
         The name of the ACL to evaluate.

      Returns
      -------
      new_acl_members : list of str
         A list of ACL members which are either a predefined ACL or an address-list element (in the sense of named.conf).

      Raises
      ------
      KeyError
         In case the specified `acl_name` does not exist in the configuration.
      """
      named_conf = self.__named_conf

      # see if ACL has been evaluated before
      if name_of_acl in self.__evaluated_acls:
         return self.__evaluated_acls[name_of_acl]

      # get ACL definition
      predefined_acls = [ '"none"', '"any"', '"localhost"', '"localnets"' ]
      logger.trace("evaluate_acl : Evaluating ACL " + name_of_acl)
      for acl in named_conf["acls"]:
         if acl["acl_name"] == name_of_acl:
            new_acl_members = []
            current_acl_members = acl["members"]
            # check each member of the ACL and add to new member list
            for current_member in current_acl_members:
               logger.trace("evaluate_acl : Checking member '" + current_member + "' of '" + name_of_acl + "'")
               if current_member in predefined_acls:
                  new_acl_members.append(current_member)
               else:
                  match = re.search('^"(.*)"$', current_member)
                  if match:
                     # if other ACL is referenced evaluate it first
                     referenced_acl_name = match.group(1)
                     for new_member in self.evaluate_acl(referenced_acl_name):
                        new_acl_members.append(new_member)
                  else:
                     new_acl_members.append(current_member)
            # save result for future use before returning it
            self.__evaluated_acls[name_of_acl] = new_acl_members
            return new_acl_members

      # unknown ACL name
      raise KeyError("ACL \"" + name_of_acl + "\" not in current configuration")


   def get_acl(self, acl_name):
      """
      Get the definition of one specific acl.

      Parameters
      ----------
      acl_name : str
         Name of the ACL whose configuration is needed.

      Returns
      -------
      acl : dict
         Representation of the requested ACL, see `get_config` for elements of ACLs.
         If the ACL does not exist, returns `None` instead.
      """

      # iterate through "acls" to find the one with the given name
      named_conf = self.__named_conf
      if "acls" in named_conf:
         for acl in named_conf["acls"]:
            if acl["acl_name"] == acl_name:
               return acl
      return None

   def get_acls(self):
      """
      Get the definition of all ACLs.

      Returns
      -------
      list of dict
         A list representing all the ACLs in named.conf, see `get_config` for details.
         Returns `None` if no ACLs are defined.
      """

      # if ACLs are present return them
      named_conf = self.__named_conf
      if "acls" in named_conf:
         return named_conf["acls"]
      else:
         return None

   def get_members(self, conf_item):
      """
      Get the members list of an ACL or an option that refers to ACLs or IP lists (e.g. allow-update, forwarders, also-notify)

      Parameters
      ----------
      conf_item : dict
         The configuraton item for that the members are supposed to be returned, e.g.
         an ACL fetched with `get_acl` or an option fetched with `get_option`

      Returns
      -------
      members : list of str
         The "members" item of the given `conf_item` or `None` if the given configuration
         does not have any "members"
      """

      # return "members" if present
      if "members" in conf_item:
         return conf_item["members"]
      return None

   def get_option(self, conf_item, option_name):
      """
      Get one specific option from global options, view options or zone options.

      Parameters
      ----------
      conf_item : dict
         A representation of the part of the configuration that should be checked for the presence
         of the specified `option_name`. 

      Returns
      -------
      option : dict
         Representation of the option that is requested or `None` if the option is not present in the
         config specified by `config_item`.

      Example
      -------
      import nnnn_toolkit as toolkit
      named_conf = toolkit.NamedConf("/opt/qip/current/dns/named.conf")
      view_conf = named_conf.get_view("external")
      option = named_conf.get_option(view, "allow-update")
      if not option:
         print("option allow-update not found in view")
      """

      # iterate through "options" to fine the one with the given name
      if "options" in conf_item:
         for option in conf_item["options"]:
            if option["option_name"] == option_name:
               return option
      return None

   def get_options(self):
      """
      Get the list of global options (i.e. in "options" block in named.conf).

      Returns
      -------
      list of dict
         All options set on global level.
      """

      # return "options" - always present
      return self.__named_conf["options"]

   def get_view(self, view_name):
      """
      Get the definition of one specific view.

      Parameters
      ----------
      view_name : str
         The name of the view whose configuration is needed.

      Returns
      -------
      view : dict
         The representation of the specified view's configuration, see `get_config` for details
         or none if the specified `view_name` does not exist.
      """

      # iterate though views to find the one with the given name
      named_conf = self.__named_conf
      for view in named_conf["views"]:
         if view["view_name"] == view_name:
            return view
      return None

   def get_views(self):
      """
      Get the definition of all views.

      Returns
      -------
      list of dict
         All views present in named.conf or `None` if no views are defined.
      """

      # return all views if present
      named_conf = self.__named_conf
      if "views" in named_conf:
         return named_conf["views"]
      else:
         return None

   def get_zone(self, view_name, zone_name):
      """
      Get the definition of one specific zone.

      Parameters
      ----------
      view_name : str
         Name of the view to which the zone belongs.
      zone_name : str
         Name of the zone whose configuration is returned.

      Returns
      -------
      dict
         Configuration of the specified zone in the specified view or `None` if either
         the `view_name` is not in named.conf or `zone_name` does not exist within
         the specified view.
      """

      # iterate through views to find the one specified
      named_conf = self.__named_conf
      for view in named_conf["views"]:
         if view["view_name"] == view_name:
            # iterate through zones to find the one specified
            if "zones" in view:
               for zone in view["zones"]:
                  if zone["zone_name"] == zone_name:
                     return zone
      return None

   def get_zones(self, view_name):
      """
      Get the definition of all zones within a view.

      Parameters
      ----------
      view_name : str
         Name of the view whos zones are needed.

      Returns
      -------
      list of dict
         Configuration for all zones in the specified view or `None` if the view does not exist.
      """

      # iterate through views to find the one specified
      named_conf = self.__named_conf
      for view in named_conf["views"]:
         if view["view_name"] == view_name:
            if "zones" in view:
               return view["zones"]
      return None

   def get_key(self, key_name):
      """
      Get one specific key.

      Parameters
      ----------
      key_name : str
         Name of the key whose configuration is needed.

      Returns
      -------
      key : dict
         The configuration of the key specified or None if the key does not exist.
      """

      # iterate through keys to find the one specified
      named_conf = self.__named_conf
      if "keys" in named_conf:
         for key in named_conf["keys"]:
            if key["key_name"] == key_name:
               return key
      return None

   def get_keys(self):
      """
      Get all keys in config.

      Returns
      -------
      list of dict
         Configuration for all keys present in named.conf or `None` if no keys exist.
      """

      # return "keys" if present
      named_conf = self.__named_conf
      if "keys" in named_conf:
         return named_conf["keys"]
      return None


   def acl_is_predefined(self, acl_members, predefined_acl, acl_name = None): 
      """
      Check if an ACL evaluates to "none", "any", "localhost" or "localnets".
      This is useful to check if a certain option (e.g. allow-update) evaluates
      to its default value.

      Example named.conf:

         acl "never" { "none"; };
         allow-update { "never"; };

            which is equal to:

         allow-update { "none" };

      Parameters
      ----------
      acl_members : list of str
         The "members" list of an ACL or of an option refering to ACLs (e.g. allow-update)
      predefined_acl : str
         One of the predefined ACL values against that the actual value of the ACL will be checked.
      acl_name : str, optional
         The name of the ACL to be checked. While it is optional to specify the ACL name it
         speeds up checking as the result will be saved to avoid duplicate checking if the
         same ACL name is checked multiple times.

      Returns
      -------
      result : boolean
         True if the specified ACL's configuration evaluates to the specified predefined ACL.

      Example
      -------
      # check if global allow-update evaluates to "none"
      import nnnn_toolkit as toolkit
      named_conf = toolkit.NamedConf("/opt/qip/current/dns/named.conf")
      named_conf_settings = named_conf.get_config()
      option = named_conf.get_option(named_conf_settings, "allow-update")
      members = named_conf.get_members(option)
      if named_conf.acl_is_predefined(members, "none"):
         print("allow-update is set to 'none'")
      """
      result = False

      # see if ACL has already been checked
      if acl_name and acl_name in self.__acl_predefined and predefined_acl in self.__acl_predefined[acl_name]:
         logger.trace("Namedconf.acl_is_predefined : ACL '" + acl_name + "' has been checked for '" + predefined_acl + "' already")
         return self.__acl_predefined[acl_name][predefined_acl]

      # check if the ACL evaluates to the given predefefined ACL
      logger.trace("Namedconf.acl_is_predefined : checking members : " + str(acl_members))
      # enforce lower case
      predefined_acls = [ "any", "none", "localhost", "localnets" ]
      if predefined_acl not in predefined_acls:
         result = False
      else:
         predefined_acls.remove(predefined_acl)
         # more than one entry -> not predefined
         if len(acl_members) != 1:
            result = False
         # one entry only
         else:
            # it's exactly the predefined value
            acl_value = acl_members[0]
            if acl_value.lower() == '"' + predefined_acl + '"':
               result = True
            # else see if it's a custom ACL
            else:
               match = re.search('^"(.*)"$', acl_value)
               if match:
                  acl_name = match.group(1)
                  # one of the other predefined ACLs?
                  if acl_name.lower() in predefined_acls:
                     result = False
                  # custom ACL - need to check this via recursive call
                  else:
                     acl_conf = self.get_acl(acl_name)
                     result = self.acl_is_predefined(acl_conf["members"], predefined_acl, acl_name)
               else:
                  result = False

      # save check result for re-use
      if acl_name:
         if acl_name not in self.__acl_predefined:
            self.__acl_predefined[acl_name] = {}
         self.__acl_predefined[acl_name][predefined_acl] = result

      # done
      return result
      

   def option_is_value(self, view_name, zone_name, option_name, required_value, default_value = None):
      """
      Check if the effective value for an option that will be applied to a zone  has a certain required_value. 
      If the option is not set at all (zone/view/global level) then the required_value will be checked against 
      the corresponding default value.

      For ACL-related options (allow-*, match-clients) currently only supports checks against a required_value 
      that is a predefined ACL (e.g. none, any).

      Parameters
      ----------
      view_name : str
         Name of the view that contains the zone to check for a specific option.
      zone_name : str
         Name of the zone of which the option will be checked.
      option_name : str
         Name of the option (e.g. allow-update, notify) that will be checked.
      required_value : str
         The effective value for the option that is required to apply for the zone.
      default_value : str, optional
         The default value to check against.

      Returns
      -------
      boolean
         True if the `required_value` is effectively used for the zone, False if not.

      Raises
      ------
      KeyError
        If the specified view or zone are not found in the current configuration or
        if an option has neither "members" or an "option_value".
      """

      named_conf = self.__named_conf

      # get configuration of zone and view 
      view_conf = self.get_view(view_name)
      if not view_conf:
         raise KeyError("view " + view_name + " not found in configuration")
      zone_conf = self.get_zone(view_name, zone_name)
      if not zone_conf:
         raise KeyError("zone " + zone_name + " [view: " + view_name + "] not found in configuration")

      # get default if not specified
      if not default_value:
         default_value = self.get_option_default(option_name)

      # check for options in this order
      levels = [ "zone", "view", "global" ]
      conf = {
         "zone" : zone_conf,
         "view" : view_conf,
         "global" : named_conf
      }

      # check if option is present on level, if yes, verify option_value or list_of_members
      for level in levels:
         logger.trace("NamedConf.option_is_value : checking option " + option_name + " on " + level + " level for zone " + zone_name + " [view : " + view_name + "]")
         zone_option = self.get_option(conf[level], option_name)
         if zone_option:
            if "members" in zone_option:
               if self.acl_is_predefined(zone_option["members"], required_value):
                  return True
               else:
                  return False
            elif "option_value" in zone_option:
               return required_value == zone_option["option_value"]
            else:
               raise KeyError("option " + option_name + "for zone " + zone_name + " [view: " + view_name + "] has no members / option_value on " + level + " level")

      # if not set at all compare against default
      logger.trace("NamedConf.option_is_value : checking option " + option_name + " versus default (" + default_value + ")")
      return required_value == default_value

   def is_dynamic(self, view_name, zone_name):
      """
      Check if a zone is dynamic (allows dynamic DNS updates) by evaluating allow-update and update-policy. 
      
      The evaluation will first consider update-policy on zone, view and global level. 
      If update-policy is present on one level the zone is considered to be dynamic. 
      If update-policy is not present allow-update will be evaluated on zone, view and global level to
      check if allow-update evaluates to "none". If it evaluates to a different value the zone is
      considered dynamic.

      Parameters
      ----------
      view_name : str
         The name of the view to that the zone belongs that will be checked.
      zone_name : str
         The name of the zone to be checked.

      Returns
      -------
      dynamic : boolean
         False if the zone does not allow any dynamic DNS updates, True otherwise.
      """

      dynamic = True

      # see if zone has already been checked
      if zone_name in self.__zone_dynamic_status and view_name in self.__zone_dynamic_status[zone_name]:
         logger.trace("is_dynamic : zone '" + zone_name + "' in view '" + view_name + "' has been checked already")
         return self.__zone_dynamic_status[zone_name][view_name]

      named_conf = self.__named_conf

      # check if update-policy is not set at all
      if self.option_is_value(view_name, zone_name, "update-policy", ""):
         # check if allow-update evaluates to "none" (either by explicit setting or because the default applies)
         if self.option_is_value(view_name, zone_name, "allow-update", "none"):
            dynamic = False
         else:
            dynamic = True
      # assuming if update-policy is used, it has at least one grant statement (otherwise would be useless) and the zone therefore is dynamic
      else:
         dynamic = True

      # save check result for re-use
      if zone_name not in self.__zone_dynamic_status:
         self.__zone_dynamic_status[zone_name] = {}
      self.__zone_dynamic_status[zone_name][view_name] = dynamic

      # done
      return dynamic

   def get_records(self, view_name, zone_name):
      """
      Use named-checkzone to convert the zone file to a standard format. Then parse zone file contents and
      return them as dict object.

      Only works for primary zones.

      Parameters
      ----------
      view_name : str
         The name of the view to that the zone belongs that will be checked.
      zone_name : str
         The name of the zone to be checked.

      Returns
      -------
      records : dict
         Represenation of all DNS records in the zone using the following structure
         {
            "owner1": {
               "record_type1": {
                  "ttl": ttl
                  "rdata": [ rdata1, rdata2, ... ]
               },
               ...
            },
            ...
         }

      """

      check_zone = 'named-checkzone'
      found = False
      bin_dirs = ('/opt/qip/current/usr/bin', '/opt/qip/usr/bin')
      for bin_dir in bin_dirs:
         check_zone_path = os.path.join(bin_dir,check_zone)
         if os.path.exists(check_zone_path):
            found = True
            break
      if not found:
            raise SystemError("get_records: cannot determine path to named-checkzone")

      zone = self.get_zone(view_name, zone_name)
      if not zone:
         raise KeyError("get_records: cannot find zone {}/{}".format(view_name, zone_name))

      zone_type = zone["zone_type"]
      zone_file_path = zone["zone_file_path"]
      if zone_type not in ("primary", "master"):
         raise ValueError("get_records: cannot get records for zone type {}".format(zone_type))

      # normalize zone file to make parsing easier
      zone_file_path_tmp = "{}.get_records".format(zone_file_path)
      command = check_zone_path
      command_args = ("-w", self.__change_dir, "-i", "local", "-k", "ignore", "-o", zone_file_path_tmp, zone_name, zone_file_path)
      (error,stdout,stderr) = run_command(command, command_args)
      if (error):
         raise SystemError("get_records: normalizing zone file using '{}' failed with error code {} : {}".format(command, error, stderr))

      # read normalized file
      records = {}

      with open(zone_file_path_tmp) as fh:
         text = fh.read()
      os.remove(zone_file_path_tmp)

      for line in text.split("\n"):
         if line == "":
            continue
         (rr_owner,rr_ttl,rr_class,rr_type,rr_rdata) = re.split("\s+", line, maxsplit=4)
         rr_owner = re.sub("\.$", "", rr_owner)
         rr_rdata = re.sub("\.$", "", rr_rdata)
         if rr_owner not in records:
            records[rr_owner] = {}
         if rr_type not in records[rr_owner]:
            records[rr_owner][rr_type] = { "ttl": rr_ttl, "rdata": [ rr_rdata ] }
         else:
            records[rr_owner][rr_type]["rdata"].append(rr_rdata)

      return records


##
## DHCP specific 
##

class DhcpdConf:
   """
   Provides easy access to dhcpd.conf and dhcpd.pcy contents.
   """

   def __init__(self, dhcpd_conf_dir, file_name="dhcpd.conf", pcy_file_name="dhcpd.pcy"):
      """
      Read and parse dhcpd.conf and dhcpd.pcy to be able to provide easy access to configuration elements 
      or the whole configuration.
      See `get_config` for a description of how to access the elements of the configuration.
      See `get_pcy` for a description of how to access the elements of the policy file.

      Parameters
      ----------
      dhcpd_conf_dir : str
         The (absolute) path to the drectory that containts the dhcpd.conf file to be read.
      file_name : str, optional
         The name of the dhcpd configuration file to be read, defaults to "dhcpd.conf".
         Set to `None` if reading/parsing of the dhcpd.conf should be skipped.
      pcy_file_name : str, optional
         The name of the dhcpd policy to be read, defaults to "dhcpd.pcy".
         Set to `None` if reading/parsing of the dhcpd.pcy should be skipped.

      Raises
      ------
      SyntaxError
         If an error is found while parsing dhcpd.conf.
      OSError
         If there are problems accessing the configuration file or the policy file.
      """
  
      # set up paths etc
      self.__dhcpd_conf_dir = dhcpd_conf_dir
      self.__file_name = file_name
      self.__pcy_file_name = pcy_file_name
      if file_name:
         dhcpd_conf_path = dhcpd_conf_dir + "/" + file_name
      else:
         dhcpd_conf_path = None
      if pcy_file_name:
         dhcpd_pcy_path = dhcpd_conf_dir + "/" + pcy_file_name
      else:
         dhcpd_pcy_path = None

      # hierarchy elements / levels
      self.__top = "top"
      self.__primary = "primary"
      self.__shared_networks = "shared-networks"
      self.__subnets = "subnets"
      self.__ranges = "ranges"
      self.__client_classes = "client-classes"
      self.__fingerprints = "excluded-fingerprints"
      self.__mac_pools = "mac-pool"
      self.__x_mac_pools = "x-mac-pool"
      self.__options = "options"
      self.__policies = "policies"

      # other class variables
      self.__dhcpd_conf = None
      self.__dhcpd_pcy = None
      self.__indent = []
      self.__v6 = False

      # setup indent - will be used when dumping dhcpd.conf back to text
      indent_width = 3
      indent_str = ""
      for level in range(10):
         for i in range(indent_width):
            indent_str += " "
         self.__indent.append(indent_str)
  
      if dhcpd_conf_path:
         # Note: even if the exception is not handled we use try/except/raise so it is easier
         #    to understand where in the code a certain Exception might be triggered
         try:
            with open(dhcpd_conf_path) as fd_dhcpd_conf:
               config_dhcpd = fd_dhcpd_conf.read()
         except OSError as error:
            raise
      
         # parse dhcpd.conf
         lines = config_dhcpd.split("\n")
         dhcpd_conf = {}
         dhcpd_conf["file_name"] = dhcpd_conf_path
         line_cnt = 0
         counters = {}
         hierarchy = [ self.__top ]
         range_types = []
         is_failover = False
         for line in lines:
            line_cnt += 1
            ###print("XXX {} {} {}".format(hierarchy[-1], line_cnt, line))
   
            ### server name of this server
            if hierarchy[-1] == self.__top:
               # server line
               match = re.search('^(v6-)?server-identifier\s(.*);$', line)
               if match:
                  if match.group(1) == "v6-":
                     self.__v6 = True
                     logger.trace("DhcpdConf : detected DHCPv6 at line {}".format(line_cnt))

                  server_name = match.group(2)
                  logger.trace("DhcpdConf : detected server {} at line {}".format(server_name,line_cnt))
                  # add server name
                  dhcpd_conf["server-identifier"] = server_name
                  continue
     
            ### primary server associated with a failover
            if hierarchy[-1] == self.__top or hierarchy[-1] == self.__primary:
               # primary line
               match = re.search('^primary-server\s([0-9\.]+);', line)
               if match:
                  if hierarchy[-1] != self.__primary:
                     hierarchy.append(self.__primary)
                  is_failover = True
                  server_ip = match.group(1)
                  logger.trace("DhcpdConf : detected primary {} at line {}".format(server_ip,line_cnt))
                  # add primary
                  if self.__primary not in dhcpd_conf:
                     dhcpd_conf[self.__primary] = []
                  dhcpd_conf[self.__primary].append({ "primary_server" : server_ip })
   
            ### fingerprints
            if hierarchy[-1] == self.__top or hierarchy[-1] == self.__primary or hierarchy[-1] == self.__subnets:
               # start of fingerprints
               match = re.search('^(\s+)excluded-fingerprints\s{', line)
               if match:
                  hierarchy.append(self.__fingerprints)
                  in_fingerprint = 1
                  fingerprint_indent = match.group(1)
                  logger.trace("DhcpdConf : detected start of excluded-fingerprints at line {}".format(line_cnt))
                  continue
            if hierarchy[-1] == self.__fingerprints:
               # end of fingerprints
               pattern = '^' + fingerprint_indent + "}"
               match = re.search(pattern, line)
               if match:
                  in_fingerprint = 0
                  hierarchy.pop()
                  logger.trace("DhcpdConf : detected end of excluded-fingerprints at line {}".format(line_cnt))
                  continue
               # fingerprint entry
               match = re.search('\s+([0-9,]+)', line)
               if match:
                  fingerprint = match.group(1)
                  # determine to which entity to attach the fingerprint
                  owner = dhcpd_conf
                  if self.__primary in hierarchy:
                     owner = owner[self.__primary][-1]
                  if self.__shared_networks in hierarchy:
                     owner = owner[self.__shared_networks][-1]
                  if self.__subnets in hierarchy:
                     owner = owner[self.__subnets][-1]
                  # add fingerprints
                  if self.__fingerprints not in owner:
                     owner[self.__fingerprints] = []
                  owner[self.__fingerprints].append(fingerprint)
                  continue
   
            ### MAC Pools
            if hierarchy[-1] == self.__top or hierarchy[-1] == self.__subnets:
               # start of MAC Pool
               match = re.search('^(\s+)(mac-pool|x-mac-pool)\s{', line)
               if match:
                  hierarchy.append(self.__mac_pools)
                  in_mac_pool = 1
                  mac_pool_indent = match.group(1)
                  mac_pool_type = match.group(2)
                  logger.trace("DhcpdConf : detected start of {} at line {}".format(mac_pool_type,line_cnt))
                  # determine to which entity to attach the MAC Pool
                  owner = dhcpd_conf
                  if self.__primary in hierarchy:
                     owner = owner[self.__primary][-1]
                  if self.__shared_networks in hierarchy:
                     owner = owner[self.__shared_networks][-1]
                  if self.__subnets in hierarchy:
                     owner = owner[self.__subnets][-1]
                  ###if in_subnet:
                     ###owner = dhcpd_conf["subnets"][-1]
                  ###else:
                     ###owner = dhcpd_conf
                  # add the MAC Pool 
                  if mac_pool_type not in owner:
                     owner[mac_pool_type] = []
                  continue
            if hierarchy[-1] == self.__mac_pools:
               # end of mac pool
               pattern = '^' + mac_pool_indent + "}"
               match = re.search(pattern, line)
               if match:
                  hierarchy.pop()
                  logger.trace("DhcpdConf : detected end of {} at line {}".format(mac_pool_type,line_cnt))
                  continue
               # MAC pool entry
               match = re.search('\s+([0-9a-f-\*]+)', line)
               if match:
                  mac_address = match.group(1)
                  # add MAC Address
                  owner[mac_pool_type].append(mac_address)
     
            ### Shared Networks
            if not self.__v6 and (hierarchy[-1] == self.__top or hierarchy[-1] == self.__primary):
               # Shared Networks step #1
               match = re.search('^# Name: (.*)$', line)
               if match:
                  shared_network_name = match.group(1)
                  logger.trace("DhcpdConf : detected shared network '{}' at line {}".format(shared_network_name,line_cnt))
               # Shared Networks step #2
               match = re.search('^(\s+)shared-network\s([_0-9]+)\s{', line)
               if match:
                  hierarchy.append(self.__shared_networks)
                  shared_network_indent = match.group(1)
                  shared_network_id = match.group(2)
                  logger.trace("DhcpdConf : detected start of shared network '{}' at line {}".format(shared_network_id,line_cnt))
                  # determine to which entity to attach the subnet
                  owner = dhcpd_conf
                  if self.__primary in hierarchy:
                     owner = owner[self.__primary][-1]
                  # add shared network
                  if self.__shared_networks not in owner:
                     owner[self.__shared_networks] = []
                  owner[self.__shared_networks].append({ "shared_network_name" : shared_network_name, "shared_network_id" : shared_network_id })
                  # update counters
                  if self.__shared_networks not in counters:
                     counters[self.__shared_networks] = 1
                  else:
                     counters[self.__shared_networks] += 1
            if hierarchy[-1] == self.__shared_networks:
               # end of Shared Network
               pattern = '^' + shared_network_indent + "}"
               match = re.search(pattern, line)
               if match:
                  hierarchy.pop()
                  logger.trace("DhcpdConf : detected end of shared network '{}' at line {}".format(shared_network_id,line_cnt))
   
            ### Subnets
            if hierarchy[-1] == self.__top or hierarchy[-1] == self.__primary or hierarchy[-1] == self.__shared_networks:
               # start of subnet
               match = re.search('(^\s+)subnet ([0-9\.]+) netmask ([0-9\.]+) {', line)
               if not match:
                  #      v6-subnet  fdec:9220:102a:101::/64 {
                  match = re.search('(^\s+)v6-subnet\s+([0-9a-f:]+)/([0-9]+) {', line)
               if match:
                  hierarchy.append(self.__subnets)
                  subnet_indent = match.group(1)
                  subnet_addr = match.group(2)
                  netmask = match.group(3)
                  logger.trace("DhcpdConf : detected subnet '{}' at line {}".format(subnet_addr,line_cnt))
                  # determine to which entity to attach the subnet
                  owner = dhcpd_conf
                  if self.__primary in hierarchy:
                     owner = owner[self.__primary][-1]
                  if self.__shared_networks in hierarchy:
                     owner = owner[self.__shared_networks][-1]
                  # add subnet
                  if self.__subnets not in owner:
                     owner[self.__subnets] = []
                  if self.__shared_networks in hierarchy:
                     owner[self.__subnets].append({ "subnet" : subnet_addr, "netmask" : netmask, "shared_network" : shared_network_id })
                  else:
                     owner[self.__subnets].append({ "subnet" : subnet_addr, "netmask" : netmask })
                  # update counters
                  if self.__subnets not in counters:
                     counters[self.__subnets] = 1
                  else:
                     counters[self.__subnets] += 1
                  continue
               
            if hierarchy[-1] == self.__subnets:
               # end of subnet
               pattern = '^' + subnet_indent + '}$'
               match = re.search(pattern, line)
               if match:
                  hierarchy.pop()
                  logger.trace("DhcpdConf : detected end of subnet '{}' at line {}".format(subnet_addr,line_cnt))
                  continue
   
            ### IP Ranges / Fixed Addresses
            ### Note: fixed addresses are simply treated as a different kind of range
            if hierarchy[-1] == self.__subnets:
               # start of ip range
               match = re.search('^(\s+)(v6-dynamic-dhcp|dynamic-dhcp|automatic-dhcp|automatic-bootp) range ([0-9a-f:\.]+) ([0-9a-f:\.]+) ', line)
               if match:
                  hierarchy.append(self.__ranges)
                  range_indent = match.group(1)
                  range_type = match.group(2)
                  range_start = match.group(3)
                  range_end = match.group(4)
                  logger.trace("DhcpdConf : detected " + range_type + " '" + range_start + " - " + range_end + "' at line " + str(line_cnt))
                  range_def = { "range_type" : range_type, "range_start" : range_start, "range_end" : range_end }
                  # vendor class filter for range
                  vc_match = re.search('\sclass\s"([^"]+)"\s', line)
                  if vc_match:
                     vendor_class = vc_match.group(1)
                     range_def["vendor_class"] = vendor_class
                  # user class filter for range
                  uc_match = re.search('\suserclass\s"(.*)"\s{', line)
                  if uc_match:
                     user_class = uc_match.group(1)
                     # user class might have multiple values
                     values = user_class.split('" "')
                     user_class = values
                     range_def["user_class"] = user_class
                  # determine to which entity to attach the range
                  owner = dhcpd_conf
                  if self.__primary in hierarchy:
                     owner = owner[self.__primary][-1]
                  if self.__shared_networks in hierarchy:
                     owner = owner[self.__shared_networks][-1]
                  if self.__subnets in hierarchy:
                     owner = owner[self.__subnets][-1]
                  # add range
                  if self.__ranges not in owner:
                     owner[self.__ranges] = []
                  owner[self.__ranges].append(range_def)
                  # update counters
                  if range_type not in counters:
                     counters[range_type] = 1
                  else:
                     counters[range_type] += 1
                  if range_type not in range_types:
                     range_types.append(range_type)
                  continue
   
               # start of fixed address
               match = re.search('^(\s+)(v6-manual-dhcp(-mac)?|manual-dhcp|manual-bootp) (duid )?([0-9a-f\-]+) ([0-9a-f\.:]+) ', line)
               if match:
                  hierarchy.append(self.__ranges)
                  range_indent = match.group(1)
                  range_type = match.group(2)
                  mac = match.group(5)
                  ip = match.group(6)
                  try:
                     logger.trace("DhcpdConf : detected " + range_type + " '" + ip + " / " + mac + "' at line " + str(line_cnt))
                  except TypeError:
                     print(f'"{match.group(1)}", "{match.group(2)}", "{match.group(3)}", "{match.group(4)}", "{match.group(5)}", "{match.group(6)}"')
                     exit()
                  # determine to which entity to attach the fixed address
                  owner = dhcpd_conf
                  if self.__primary in hierarchy:
                     owner = owner[self.__primary][-1]
                  if self.__shared_networks in hierarchy:
                     owner = owner[self.__shared_networks][-1]
                  if self.__subnets in hierarchy:
                     owner = owner[self.__subnets][-1]
                  # add fixed address
                  if self.__ranges not in owner:
                     owner[self.__ranges] = []
                  owner[self.__ranges].append({ "range_type" : range_type, "mac" : mac, "ip" : ip })
                  # update counters
                  if range_type not in counters:
                     counters[range_type] = 1
                  else:
                     counters[range_type] += 1
                  if range_type not in range_types:
                     range_types.append(range_type)
                  continue
   
            if hierarchy[-1] == self.__ranges:
               # end of range / fixed address
               pattern = '^' + range_indent + '}$'
               match = re.search(pattern, line)
               if match:
                  hierarchy.pop()
                  logger.trace("DhcpdConf : detected end of range at line {}".format(line_cnt))
                  continue
   
            if hierarchy[-1] == self.__top or hierarchy[-1] == self.__primary or hierarchy[-1] == self.__subnets or hierarchy[-1] == self.__ranges:
               # client classes : user / vendor class
               match = re.search('^(\s+)(user-class|vendor-class)\s"(.+)"', line)
               if match:
                  hierarchy.append(self.__client_classes)
                  class_indent = match.group(1)
                  class_type = match.group(2)
                  class_match_value = match.group(3)
                  # user-class might have multiple values
                  if class_type == "user-class":
                     values = class_match_value.split('" "')
                     class_match_value = values
                  logger.trace("DhcpdConf : detected class {} matching {} at line {}".format(class_type,class_match_value,line_cnt))
                  # determine to which entity to attach the client class
                  owner = dhcpd_conf
                  if self.__primary in hierarchy:
                     owner = owner[self.__primary][-1]
                  if self.__shared_networks in hierarchy:
                     owner = owner[self.__shared_networks][-1]
                  if self.__subnets in hierarchy:
                     owner = owner[self.__subnets][-1]
                  if self.__ranges in hierarchy:
                     owner = owner[self.__ranges][-1]
                  # add client class
                  if self.__client_classes not in owner:
                     owner[self.__client_classes] = []
                  owner[self.__client_classes].append({ "class_type" : class_type, "class_match_value" : class_match_value })
                  continue
               # client classes : option class
               match = re.search('^(\s+)(option-class)\s([0-9]+)\s"([^"]+)"', line)
               if match:
                  hierarchy.append(self.__client_classes)
                  class_indent = match.group(1)
                  class_type = match.group(2)
                  class_match_nr = match.group(3)
                  class_match_value = match.group(4)
                  logger.trace("DhcpdConf : detected class {} at line {}".format(class_type,line_cnt))
                  # determine to which entity to attach the client class
                  owner = dhcpd_conf
                  if self.__primary in hierarchy:
                     owner = owner[self.__primary][-1]
                  if self.__shared_networks in hierarchy:
                     owner = owner[self.__shared_networks][-1]
                  if self.__subnets in hierarchy:
                     owner = owner[self.__subnets][-1]
                  if self.__ranges in hierarchy:
                     owner = owner[self.__ranges][-1]
                  # add client class
                  if self.__client_classes not in owner:
                     owner[self.__client_classes] = []
                  owner[self.__client_classes].append({ "class_type" : class_type, "class_match_nr" : class_match_nr, "class_match_value" : class_match_value })
                  continue
     
            if hierarchy[-1] == self.__client_classes:
               # end of class
               pattern = '^' + class_indent + '}$'
               match = re.search(pattern, line)
               if match:
                  hierarchy.pop()
                  logger.trace("DhcpdConf : end of class {} at line {}".format(class_type,line_cnt))
                  continue
   
            if hierarchy[-1] == self.__ranges or hierarchy[-1] == self.__client_classes or hierarchy[-1] == self.__subnets:
               # options / policies
               match = re.search('^\s+(option|policy)\s(\S+)\s(.*);', line)
               if match:
                  option_type = match.group(1)
                  option_name = match.group(2)
                  option_value = match.group(3)
                  if option_type == "option":
                     key_name = self.__options
                  elif option_type == "policy":
                     key_name = self.__policies
                     # policy might have multiple values
                     values = option_value.split(", ")
                     option_value = values
                  else:
                     raise SyntaxError("Unknown configuration type {} at line {}".format(option_type, line_cnt))
                  # determine to which entity to attach the option / policy
                  owner = dhcpd_conf
                  if self.__primary in hierarchy:
                     owner = owner[self.__primary][-1]
                  if self.__shared_networks in hierarchy:
                     owner = owner[self.__shared_networks][-1]
                  if self.__subnets in hierarchy:
                     owner = owner[self.__subnets][-1]
                  if self.__ranges in hierarchy:
                     owner = owner[self.__ranges][-1]
                  if self.__client_classes in hierarchy:
                     owner = owner[self.__client_classes][-1]
                  # add option/policy
                  if key_name not in owner:
                     owner[key_name] = [] 
                  owner[key_name].append({ "{}_name".format(option_type) : option_name, "{}_value".format(option_type) : option_value })
                  logger.trace("DhcpdConf : detected {} '{}' = '{}' at line {}".format(option_type, option_name, option_value, line_cnt))
                  continue
   
            # add counters, range types and additional info for convienience
            dhcpd_conf["counters"] = {}
            for range_type in counters:
               dhcpd_conf["counters"][range_type] = counters[range_type]
            dhcpd_conf["range_types"] = range_types
            dhcpd_conf["is_failover"] = is_failover
            dhcpd_conf["has_changed"] = False
     
            # save result for later use
            self.__dhcpd_conf = dhcpd_conf

      if dhcpd_pcy_path:
         # read dhcpd.pcy
         try:
            with open(dhcpd_pcy_path) as fd_dhcpd_pcy:
               pcy_dhcpd = fd_dhcpd_pcy.read()
         except OSError as error:
            raise
   
         # parse dhcpd.pcy
         dhcpd_pcy = {}
         dhcpd_pcy["file_name"] = dhcpd_pcy_path
         dhcpd_pcy["policies"] = []
         additional_policy = False
         for line in pcy_dhcpd.split("\n"):
            # remove comments
            new_line = re.sub('[;#].*', "", line)
            # skip empty / blank lines
            if re.search('^\s*$', new_line):
               continue
            # assign values
            (key, value) = new_line.split("=")
            dhcpd_pcy["policies"].append({ "policy_name" : key, "policy_value" : value, "additional_policy" : additional_policy })
            # detected start of additional policies
            if re.search('# Begin corporate extensions', line):
               additional_policy = True
         dhcpd_pcy["has_changed"] = False

         # save result for later use
         self.__dhcpd_pcy = dhcpd_pcy


   def get_config(self):
      """
      Provide dhcpd.conf as dictionary representing the various elements of the configuration.
      Note that not all elements and options are supported.

      The dictionary consists of the following elements (if present in the dhcpd.conf configuration file):

      "server-identifier": 
         Name of the DHCP server.
         Only exists on top level.

      "primary": 
         Configuration of an associated primary server (only exists in failover servers)
         Consists of "primary_server" which is the IP address of the associated primary.
         Can also contain all other elements that can exist on top level, except MAC Pools and
         Excludeded Fingerprints as those are currently written only to the Primary configuration
         or on the top level.

      "excluded-fingerprints": 
         List of excluded fingerprints. 
         Can exists on top level (Primary DHCP Server only) or on subnet level.

      "mac-pool": 
         List of allowed MACs.
         Can exists on top level or subnet level.

      "x-mac-pool": 
         List of excluded MACs.
         Can exists on top level or subnet level.

      "shared-networks": 
         List of shared networks.
         Each shared network in the list has a "shared_network_name" (as defined in the UI) as
         well as a "shared_network_id" which is generated based on the Primary Subnet of the Shared Network
         in the format _ip1_ip2_ip3_ip4.
         Each shared network has a "subnets" entry.
         Can exist on top level.
         
      "subnets": 
         List of subnets.
         Each subnet has a "subnet" (start address) and "netmask" (subnet mask). 
         In addition "ranges" will be present and optionally "client_classes", "excluded-fingerprints",
         "mac-pool" and "x-mac-pool".
         "subnets" can exist on top or shared network level.

      "ranges":
         List of ranges or fixed addresses.
         Each range or fixed address has a "range_type".
         For ranges of type "dynamic-dhcp", "automatic-dhcp", "automatic-bootp":
            Each range has a "range_start" and "range_end". Optionally ranges might have "user_class" and/or
            "vendor_class" filters associated with them. "user_class" is a list, "vendor_class" is a single
            value.
         For fixed addresses of type "manual-dhcp", "manual-bootp": 
            Each fixed address type has a "mac" and an "ip".
         In addition each range or fixed address  might have "options", "policies" and "client_classes".
         Ranges exist on subnet level.
      
      "options":
         List of options assigned to the client.
         Each option has an "option_name" and an "option_value".
         Options exist on range or client class level.

      "policies":
         List of policies that apply to range / fixed addresses or client_classes.
         Each policy has a "policy_name" and a "policy_value", the value is a list.
         Options exist on range or client class level.

      "client-classes":
         List of client classes.
         Each client class has a "class_type" and "class_match_value". If the "class_type" is
         'option-class' the client class additionally has a "class_match_nr".
         Also the client class might have "options" and "policies".
         Client classes can exist on top, subnet or range level.

      "counters":
         A dictionary counting the various elements in the dhcpd.conf.

      "range_types":
         A list of range types (e.g. dynamic-dhcp) that appear in the dhcpd.conf.

      "is_failover":
         A boolean that allows to control if the dhcpd.conf is that of a Primary DHCP Server or of a Failover.

      "has_changed":
         This can be used to flag to another function that the configuration has been changed and needs to
         be dumped to disk. The `dump_to_file` method will only update the file on disk if this is set to True.

      "file_name":
         The full path to the dhcpd.conf file that has been used to create the configuration.
           
      Returns
      -------
      dict
         The dictionary representation of the dhcpd.conf.
      """
      return self.__dhcpd_conf

   def get_json(self):
      """
      Provide dhcpd.conf contents as JSON formatted string.
      
      Returns
      -------
      json_data : str
         Formatted (indented) JSON data representing the dhcpd.conf data.
      """

      # dump data as JSON
      json_data = json.dumps(self.__dhcpd_conf, indent = 3)
      return json_data

   def conf_has_changed(self):
      """
      Set the "has_changed" property for the current configuration to `True`.
      """
      self.__dhcpd_conf["has_changed"] = True

   def get_pcy(self):
      """
      Provide dhcpd.pcy as dictionary representing the policies.

      The dictionary consists of the following elements:

      "policies":
         List of policies.
         Each policy has a "policy_name" and a "policy_value".

      "has_changed":
         This can be used to flag to another function that the configuration has been changed and needs to
         be dumped to disk. The `dump_pcy_to_file` method will only update the file on disk if this is set to True.

      "file_name":
         The full path to the dhcpd.pcy file that has been used to create the configuration.

      Returns
      -------
      dict
         The dictionary representation of the dhcpd.conf.
      """
      return self.__dhcpd_pcy

   def get_json_pcy(self):
      """
      Provide dhcpd.pcy contents as JSON formatted string.
      
      Returns
      -------
      json_data: str
         Formatted (indented) JSON data representing the dhcpd.pcy policies.
      """

      # dump pcy as JSON
      json_data = json.dumps(self.__dhcpd_pcy, indent = 3)
      return json_data

   def pcy_has_changed(self):
      """
      Set the "has_changed" property for the current policy to `True`.
      """
      self.__dhcpd_pcy["has_changed"] = True

   def get_range_types(self):
      """
      Return the list of range types in a configuration.

      Returns
      -------
      list of str
      """
      return self.__dhcpd_conf["range_types"]

   def get_list(self, conf_item, owner_config):
      """
      Get the child elements of a configuration element.

      Params
      ------
      conf_item : str
         The name of the configuration item for that the 
         list items are returned.
      owner_config : dict
         The configuration item of which the child elements
         are needed.

      Returns
      -------
      item_list : list
         List of items / child elements of the given configuration.
         Might be empty if there are no child elements.
      """

      item_list = []
      # iterate through list
      if conf_item in owner_config:
         for item in owner_config[conf_item]:
            item_list.append(item)
      return item_list

   def get_macs(self, mac_pool_type="mac-pool", owner_config=None):
      """
      Get the MACs of the specified MAC Pool type.

      Parameters
      ----------
      mac_pool_type : str, optional
         Specify the type of MAC Pool to get. Allowed values are "mac-pool" and "x-mac-pool".
         Default is "mac-pool".
      owner_config : dict, optional
         Can be a subnet configuration or a complete dhcpd configuration as returned by `get_config`.
         If not specified the current dhcpd configuration is used.

      Returns
      -------
      mac_list : list of str
         The MACs in the MAC Pool, might be empty if there is no MAC Pool of the specified
         type in the configuration.

      Raises
      ------
      ValueError
         If an invalid value is specified for mac_pool_type.
      """

      # setup
      if not owner_config:
         owner_config = self.__dhcpd_conf
      if mac_pool_type != "mac-pool" and mac_pool_type != "x-mac-pool":
         raise ValueError("Invalid mac_pool_type '{}', must be 'mac-pool' or 'x-mac-pool'".format(mac_pool_type))

      # iterate through MACs
      return self.get_list(mac_pool_type, owner_config)

   def get_fingerprints(self, owner_config=None):
      """
      Get the excluded fingerprints.

      Parameters
      ----------
      owner_config : dict, optional
         Can be a subnet configuration or a complete dhcpd configuration as returned by `get_config`.
         If not specified the current dhcpd configuration is used.

      Returns
      -------
      fingerprint_list : list of str
         The list of fingerprints, might be empty if there are no excluded fingerprints in the specified
         configuration.
      """

      # setup
      if not owner_config:
         owner_config = self.__dhcpd_conf

      # iterate through fingerprints
      return self.get_list(self.__fingerprints, owner_config)

   def get_primaries(self, owner_config=None):
      """
      Get the primary configuration for all primaries associated with a failover
      DHCP server. 

      Parameters
      ----------
      owner_config : dict, optional
         Can be complete dhcpd configuration as returned by `get_config`.
         If not specified the current dhcpd configuration is used.

      Returns
      -------
      primary_list : list of dict
         The associated primaries' configuration, might be empty if there are no
         associated primaries.
      """

      # set up
      if not owner_config:
         owner_config = self.__dhcpd_conf
      
      # iterate through primaries
      return self.get_list(self.__primary, owner_config)

   def get_shared_networks(self, owner_config=None):
      """
      Get all the shared network's configurations.

      Parameters
      ----------
      owner_config : dict, optional
         Can be complete dhcpd configuration as returned by `get_config`
         or a primary's configuration.
         If not specified the current dhcpd configuration is used.

      Returns
      -------
      shared_network_list : list of dict
         The shared network's configurations or `None` if there
         are no shared networks.
      """

      # set up
      if not owner_config:
         owner_config = self.__dhcpd_conf

      # iterate through shared networks
      return self.get_list(self.__shared_networks, owner_config)

   def get_subnets(self, shared_network_id=None, include_shared_networks=True, owner_config=None):
      """
      Get all subnet configurations from the DHCP configuration or just the ones
      from one specific shared network.

      Parameters
      ----------
      shared_network_id - str
         ID of the shared network for that the list of subnets
         is returned. Default is `None`.
      include_shared_networks - boolean
         Wether to include the subnets within shared networks in the list. Default is True.
      owner_config : dict, optional
         Can be complete dhcpd configuration as returned by `get_config` or one primaries configuration
         or a shared network's configuration.
         If not specified the current dhcpd configuration is used.

      Returns
      -------
      list
         A list of subnet representations from the dhcpd.conf.
         Might be empty if there are no subnets.
      """

      # set up
      if not owner_config:
         owner_config = self.__dhcpd_conf

      # create list of configurations
      conf_list = []

      # primary vs. failover config
      if "is_failover" in owner_config and owner_config["is_failover"]:
         # primaries asscociated with failover
         for primary_conf in owner_config["primary"]:
            conf_list.append(primary_conf)
      else:
         # primary config
         conf_list.append(owner_config)

      # create list of subnets
      subnet_conf_list = []

      # iterate through configuration
      for conf in conf_list:
         # add all subnets outside shared networks if required
         if "subnets" in conf and not shared_network_id:
            for subnet_conf in conf["subnets"]:
               subnet_conf_list.append(subnet_conf)
         # add all subnets inside shared networks ...
         if "shared-networks" in conf and include_shared_networks:
            for network_conf in conf["shared-networks"]:
               # ... or only the ones from one specific shared network
               if shared_network_id:
                  if network_conf["shared_network_id"] != shared_network_id:
                     continue
               if "subnets" in network_conf:
                  for subnet_conf in network_conf["subnets"]:
                     subnet_conf_list.append(subnet_conf)

      # done
      return subnet_conf_list

   def get_ranges(self, subnet_config):
      """
      Get all ranges within a subnet.

      Parameters
      ----------
      subnet_config : dict
         The subnet of which to get the associated ranges.

      Returns
      -------
      range_list : list of dict
         The list of range configurations, might be empty if there are no
         ranges in the subnet (should never be the case).
      """

      # iterate through ranges
      return self.get_list(self.__ranges, subnet_config)

   def get_client_classes(self, owner_config=None):
      """
      Get all client classes associated with a DHCP Server, a subnet
      or a range.

      Parameters
      ----------
      owner_config : dict, optional
         Can be complete dhcpd configuration as returned by `get_config` or
         a subnet's or a range's configuration.
         If not specified the current dhcpd configuration is used.

      Returns
      -------
      client_class_list : list of dict
         The list of client class configurations, might be empty if there are
         no client classes.
      """

      # setup
      if not owner_config:
         owner_config = self.__dhcpd_conf
      client_class_list = []

      # iterate through client classes
      return self.get_list(self.__client_classes, owner_config)

   def get_options(self, owner_config):
      """
      Get all options of a range or a client class.

      Parameters
      ----------
      owner_config : dict
         Can be a range or a client class configuration.

      Returns
      -------
      option_list : list of dict
         The list of options for the range or client class,
         might be empty if there are no options.
      """
      
      # iterate through options
      return self.get_list(self.__options, owner_config)

   def get_policies(self, owner_config):
      """
      Get all policies or a range or a client class.

      Parameters
      ----------
      owner_config : dict
         Can be a range or a client class configuration.

      Returns
      -------
      option_list : list of dict
         The list of options for the range or client class,
         might be empty if there are no options.
      """
      
      # iterate through options
      return self.get_list(self.__policies, owner_config)

   def diff_options(self, my_conf, other_conf, name="Option", missing_only=False):
      """
      Compare the DHCP options of two configuration items, e.g. ranges, client classes.

      Parameters
      ----------
      my_conf : dict
         Reference configuration element to compare.
      other_conf : dict
         Configuration to compare with.
      name : str
         Name to add to the `diff_messages` that report the differences found.
      missing_only : boolean
         Controls if to report missing items only when comparing the list or
         also report different values.
      """
      # options
      my_options = self.get_options(my_conf)
      other_options = self.get_options(other_conf)
      primary_key = "option_name"
      additional_keys = [ "option_value" ]
      (diff_messages, diff_data) = diff_list(my_options, other_options, name=name, primary_key=primary_key, additional_keys=additional_keys, missing_only=missing_only)
      return (diff_messages, diff_data)

   def diff_policies(self, my_conf, other_conf, name="Policy", missing_only=False):
      """
      Compare the DHCP policies of two configuration items, e.g. ranges, client classes.

      Parameters
      ----------
      my_conf : dict
         Reference configuration element to compare.
      other_conf : dict
         Configuration to compare with.
      name : str
         Name to add to the `diff_messages` that report the differences found.
      missing_only : boolean
         Controls if to report missing items only when comparing the list or
         also report different values.
      """
      # policies
      my_policies = self.get_policies(my_conf)
      other_policies = self.get_policies(other_conf)
      primary_key = "policy_name"
      additional_keys = [ "policy_value" ]
      (diff_messages, diff_data) = diff_list(my_policies, other_policies, name=name, primary_key=primary_key, additional_keys=additional_keys, missing_only=missing_only)
      return (diff_messages, diff_data)

   def diff_client_classes(self, my_conf, other_conf, name="Client Class", missing_only=False):
      """
      Compare the Client Classes assigned to two configuration items, e.g. DHCP Server,
      Subnet, Fixed Address.

      Parameters
      ----------
      my_conf : dict
         Reference configuration element to compare.
      other_conf : dict
         Configuration to compare with.
      name : str
         Name to add to the `diff_messages` that report the differences found.
      missing_only : boolean
         Controls if to report missing items only when comparing the list or
         also report different values.
      """
      # client classes
      my_client_classes = self.get_client_classes(my_conf)
      other_client_classes = self.get_client_classes(other_conf)

      diff_messages = []
      diff_data = {}
      keys = [ "same", "missing", "diff" ]
      for key in keys:
         diff_data[key] = []

      # check user and vendor class
      client_class_pkey = "class_match_value"
      for class_type in [ "user-class", "vendor-class" ]:
         my_classes = get_list_items(my_client_classes, "class_type", class_type)
         other_classes = get_list_items(other_client_classes, "class_type", class_type)
         (tmp_diff_messages, tmp_diff_data) = diff_list(my_classes, other_classes, name=name, primary_key=client_class_pkey, missing_only=missing_only)
         diff_messages.extend(tmp_diff_messages)
         for key in keys:
            diff_data[key].extend(tmp_diff_data[key])

         # compare child elements for same and different user / vendor classes
         for my_client_class_conf in my_classes:
            descend = False
            client_class = my_client_class_conf[client_class_pkey]
            if client_class in tmp_diff_data["same"]:
               descend = True
            else:
               if get_list_item(tmp_diff_data["diff"], client_class_pkey, client_class):
                  descend = True
            if not descend:
               continue
            other_client_class_conf = get_list_item(other_classes, client_class_pkey, client_class)
      
            # options
            option_name = "{} ({}) Option".format(name, class_type)
            (tmp_diff_messages, option_diff_data) = self.diff_options(my_client_class_conf, other_client_class_conf, name=option_name, missing_only=missing_only)
            diff_messages.extend(tmp_diff_messages)
      
            # policies
            policy_name = "{} ({}) Policy".format(name, class_type)
            (tmp_diff_messages, policies_diff_data) = self.diff_policies(my_client_class_conf, other_client_class_conf, name=policy_name, missing_only=missing_only)
            diff_messages.extend(tmp_diff_messages)

      # check option class
      class_type = "option-class"
      my_classes = get_list_items(my_client_classes, "class_type", class_type)
      other_classes = get_list_items(other_client_classes, "class_type", class_type)
      client_class_pkey = "class_match_nr"
      additional_keys = [ "class_match_value" ]
      (tmp_diff_messages, tmp_diff_data) = diff_list(my_classes, other_classes, name=name, primary_key=client_class_pkey, additional_keys=additional_keys, missing_only=missing_only)
      diff_messages.extend(tmp_diff_messages)
      for key in keys:
         diff_data[key].extend(tmp_diff_data[key])

      # compare child elements for same and different option classes
      for my_client_class_conf in my_classes:
         descend = False
         client_class = my_client_class_conf[client_class_pkey]
         if client_class in tmp_diff_data["same"]:
            descend = True
         else:
            if get_list_item(tmp_diff_data["diff"], client_class_pkey, client_class):
               descend = True
         if not descend:
            continue
         other_client_class_conf = get_list_item(other_classes, client_class_pkey, client_class)
   
         # options
         option_name = "{} ({}) Option".format(name, class_type)
         (tmp_diff_messages, option_diff_data) = self.diff_options(my_client_class_conf, other_client_class_conf, name=option_name, missing_only=missing_only)
         diff_messages.extend(tmp_diff_messages)
   
         # policies
         policy_name = "{} ({}) Policy".format(name, class_type)
         (tmp_diff_messages, policies_diff_data) = self.diff_policies(my_client_class_conf, other_client_class_conf, name=policy_name, missing_only=missing_only)
         diff_messages.extend(tmp_diff_messages)
  
      # done
      return (diff_messages, diff_data)

   def diff_fingerprints(self, my_conf, other_conf, name="Fingerprints", missing_only=False):
      """
      Compare the Excluded Fingerprints of two configutation items, e.g. DHCP Server or Subnet.

      Parameters
      ----------
      my_conf : dict
         Reference configuration element to compare.
      other_conf : dict
         Configuration to compare with.
      name : str
         Name to add to the `diff_messages` that report the differences found.
      missing_only : boolean
         Controls if to report missing items only when comparing the list or
         also report different values.
      """
      # excluded-fingerprints
      my_fingerprints = self.get_fingerprints(my_conf)
      other_fingerprints = self.get_fingerprints(other_conf)
      (diff_messages, diff_data) = diff_list(my_fingerprints, other_fingerprints, name=name, missing_only=missing_only)
      return (diff_messages, diff_data)

   def diff_macs(self, my_conf, other_conf, mac_pool_type, name="MAC Pool", missing_only=False):
      """
      Compare the (Exclude) MAC Pools of two configutation items, e.g. DHCP Server or Subnet.

      Parameters
      ----------
      my_conf : dict
         Reference configuration element to compare.
      other_conf : dict
         Configuration to compare with.
      name : str
         Name to add to the `diff_messages` that report the differences found.
      missing_only : boolean
         Controls if to report missing items only when comparing the list or
         also report different values.
      """
      # mac-pool / x-mac-pool
      my_mac_pool = self.get_macs(mac_pool_type=mac_pool_type, owner_config=my_conf)
      other_mac_pool = self.get_macs(mac_pool_type=mac_pool_type, owner_config=other_conf)
      (diff_messages, diff_data) = diff_list(my_mac_pool, other_mac_pool, name=name, missing_only=missing_only)
      return (diff_messages, diff_data)

   def diff_conf(self, other, missing_only=False):
      """
      Check for differences between two DHCP configurations.

      The comparison will be one way, where the current configuration will be the 
      reference to that the `other` configuration will be compared to.

      Parameters
      ----------
      other : nnnn_toolkit.DhcpdConf
         The configuration to compare the current configuration to.
      missing_only : boolen
         Control if to report all differences or only the missing configuration items.

      Returns
      -------
      diff : array of str
         The list of differences found between the two configurations.
      """

      # TODO improve options/policies for client classes

      diff = []
      my_conf = self.get_config()
      other_conf = other.get_config()

      # check if we are comparing silimar servers
      if my_conf["is_failover"] != other_conf["is_failover"]:
         diff.append("Cannot compare Primary with Failover DHCP configuration")
         return diff

      # compare global stuff

      # global Fingerprints
      name = "Global Excluded Fingerprints"
      (diff_messages, diff_data) = self.diff_fingerprints(my_conf, other_conf, name=name, missing_only=missing_only)
      diff.extend(diff_messages)

      # global MAC Pool
      name = "MAC from Global MAC Pool"
      (diff_messages, diff_data) = self.diff_macs(my_conf, other_conf, mac_pool_type="mac-pool", name=name, missing_only=missing_only)
      diff.extend(diff_messages)

      # global Exclude MAC Pool
      name = "MAC from Global Exclude MAC Pool"
      (diff_messages, diff_data) = self.diff_macs(my_conf, other_conf, mac_pool_type="x-mac-pool", name=name, missing_only=missing_only)
      diff.extend(diff_messages)

      conf_list = []
      other_conf_list = []

      # handle Standalone/Primary vs. Failover
      if my_conf["is_failover"]:
         my_primaries = self.get_primaries()
         other_primaries = other.get_primaries()
         name = "Primary DHCP Server"
         primary_pkey = "primary_server"
         (diff_messages, primary_diff_data) = diff_list(my_primaries, other_primaries, name=name, primary_key=primary_pkey, missing_only=missing_only)
         diff.extend(diff_messages)
         # further compare all primaries that are present in both configurations
         for my_primary_conf in my_primaries:
            server = my_primary_conf[primary_pkey]
            if server in primary_diff_data["same"]:
               conf_list.append(my_primary_conf)
               other_primary_conf = other.get_item(other_conf, primary_pkey, server)
               other_conf_list.append(other_primary_conf)
      else:
         conf_list.append(my_conf)
         other_conf_list.append(other_conf)

      # compare remaining configuration
      for my_conf, other_conf in zip(conf_list, other_conf_list):
   
         # shared_networks
         my_shared_networks = self.get_shared_networks(my_conf)
         other_shared_networks = other.get_shared_networks(other_conf)
         name = "Shared Network"
         shared_network_pkey = "shared_network_id"
         (diff_messages, shared_network_diff_data) = diff_list(my_shared_networks, other_shared_networks, name=name, primary_key=shared_network_pkey, missing_only=missing_only)
         diff.extend(diff_messages)
        
         # subnets
         my_subnets = self.get_subnets(owner_config=my_conf)
         other_subnets = other.get_subnets(owner_config=other_conf)
         name = "Subnet"
         subnet_pkey = "subnet"
         additional_keys = [ "netmask", "shared_network" ]
         (diff_messages, subnet_diff_data) = diff_list(my_subnets, other_subnets, name=name, primary_key=subnet_pkey, additional_keys=additional_keys, missing_only=missing_only)
         diff.extend(diff_messages)
   
         # compare child elements for same and different subnets
         for my_subnet_conf in my_subnets:
            descend = False
            subnet = my_subnet_conf[subnet_pkey]
            if subnet in subnet_diff_data["same"]:
               descend = True
            else:
               if get_list_item(subnet_diff_data["diff"], subnet_pkey, subnet):
                  descend = True
            if not descend:
               continue
            other_subnet_conf = get_list_item(other_subnets, subnet_pkey, subnet)
   
            # subnet fingerprints
            name = "Subnet {} Excluded Fingerprints".format(subnet)
            (diff_messages, fingerprint_diff_data) = self.diff_fingerprints(my_subnet_conf, other_subnet_conf, name=name, missing_only=missing_only)
            diff.extend(diff_messages)
   
            # subnet mac pools
            name = "MAC from Subnet {} MAC Pool".format(subnet)
            (diff_messages, mac_pool_diff_data) = self.diff_macs(my_subnet_conf, other_subnet_conf, mac_pool_type="mac-pool", name=name, missing_only=missing_only)
            diff.extend(diff_messages)
   
            # global Exclude MAC Pool
            name = "MAC from Subnet {} Exclude MAC Pool".format(subnet)
            (diff_messages, x_mac_pool_diff_data) = self.diff_macs(my_subnet_conf, other_subnet_conf, mac_pool_type="x-mac-pool", name=name, missing_only=missing_only)
            diff.extend(diff_messages)
   
            # ranges
            my_ranges = self.get_ranges(my_subnet_conf)
            other_ranges = other.get_ranges(other_subnet_conf)
   
            # part #1 dynamic ranges
            range_types = ( 'dynamic-dhcp', 'automatic-dhcp', 'automatic-bootp' )
            for range_type in range_types:
               my_dynamic_ranges = (get_list_items(my_ranges, "range_type", range_type))
               other_dynamic_ranges = (get_list_items(other_ranges, "range_type", range_type))
               range_name = "{} Range".format(range_type.title())
               range_pkey = "range_start"
               additional_keys = [ "range_end", "vendor_class", "user_class"  ]
               (diff_messages, range_diff_data) = diff_list(my_dynamic_ranges, other_dynamic_ranges, name=range_name, primary_key=range_pkey, additional_keys=additional_keys, missing_only=missing_only)
               diff.extend(diff_messages)
   
               # compare child elements for same and different ranges part #1
               for my_range_conf in my_dynamic_ranges:
                  descend = False
                  range_id = my_range_conf[range_pkey]
                  if range_id in range_diff_data["same"]:
                     descend = True
                  else:
                     if get_list_item(range_diff_data["diff"], range_pkey, range_id):
                        descend = True
                  if not descend:
                     continue
                  other_range_conf = get_list_item(other_dynamic_ranges, range_pkey, range_id)
   
                  # options
                  name = "{} '{}' Option".format(range_name, range_id)
                  (diff_messages, option_diff_data) = self.diff_options(my_range_conf, other_range_conf, name=name, missing_only=missing_only)
                  diff.extend(diff_messages)
   
                  # policies
                  name = "{} '{}' Policy".format(range_name, range_id)
                  (diff_messages, policies_diff_data) = self.diff_policies(my_range_conf, other_range_conf, name=name, missing_only=missing_only)
                  diff.extend(diff_messages)
   
                  # client classes
                  name = "{} '{}' Client Class".format(range_name, range_id)
                  (diff_messages, policies_diff_data) = self.diff_client_classes(my_range_conf, other_range_conf, name=name, missing_only=missing_only)
                  diff.extend(diff_messages)
   
            # part #2 fixed addresses
            fixed_address_types = ( 'manual-dhcp', 'manual-bootp' )
            for fixed_address_type in fixed_address_types:
               my_fixed_addresses = get_list_items(my_ranges, "range_type", fixed_address_type)
               other_fixed_addresses = get_list_items(other_ranges, "range_type", fixed_address_type)

               fixed_addresses_name = "{} IP".format(fixed_address_type.title())
               range_pkey = "ip"
               additional_keys = [ "mac" ]
               (diff_messages, range_diff_data) = diff_list(my_fixed_addresses, other_fixed_addresses, name=fixed_addresses_name, primary_key=range_pkey, additional_keys=additional_keys, missing_only=missing_only)
               diff.extend(diff_messages)
   
               # compare child elements for same and different ranges part #2
               for my_fixed_address_conf in my_fixed_addresses:
                  descend = False
                  fixed_address = my_fixed_address_conf[range_pkey]
                  if fixed_address in range_diff_data["same"]:
                     descend = True
                  else:
                     if get_list_item(range_diff_data["diff"], range_pkey, fixed_address):
                        descend = True
                  if not descend:
                     continue
                  other_fixed_address_conf = get_list_item(other_fixed_addresses, range_pkey, fixed_address)
   
                  # options
                  name = "{} '{}' Option".format(fixed_addresses_name, fixed_address)
                  (diff_messages, option_diff_data) = self.diff_options(my_fixed_address_conf, other_fixed_address_conf, name=name, missing_only=missing_only)
                  diff.extend(diff_messages)
   
                  # policies
                  name = "{} '{}' Policy".format(fixed_addresses_name, fixed_address)
                  (diff_messages, policies_diff_data) = self.diff_policies(my_fixed_address_conf, other_fixed_address_conf, name=name, missing_only=missing_only)
                  diff.extend(diff_messages)
   
                  # client classes
                  name = "{} '{}' Client Class".format(fixed_addresses_name, fixed_address)
                  (diff_messages, client_classes_diff_data) = self.diff_client_classes(my_fixed_address_conf, other_fixed_address_conf, name=name, missing_only=missing_only)
                  diff.extend(diff_messages)

         # client classes
         (diff_messages, client_class_diff_data) = self.diff_client_classes(my_conf, other_conf, missing_only=missing_only)
         diff.extend(diff_messages)
  
      # done
      return diff

   def is_v6(self):
      return self.__v6
   
   def diff(self, other):
      """
      Check for differences between two DHCP configurations.
      Configurations will be compared in both directions.

      Parameters
      ----------
      other : nnnn_toolkit.DhcpdConf
         The configuration to compare the current configuration to.

      Returns
      -------
      diff : array of str
         The list of differences found between the two configurations.
      """

      diff_messages = []
      for message in self.diff_conf(other):
         diff_messages.append("> " + message)
      for message in other.diff_conf(self, missing_only=True):
         diff_messages.append("< " + message)
      return diff_messages

   def __dump_list(self, list_name, list_items, list_indent, item_indent):
      """
      Used internally by the dump method to dump a list of configuration items,
      e.g. list of MACs in MAC Pools, list of fingerprints, list of user classes etc.

      Params
      ------
      list_name : str
         The name of the configuration element.
      list_items : list of str
         The list to dump.
      list_indent : int
         Level of indentation for the list name.
      item_indent : str
         Level of identation for the items of the list.

      Returns
      -------
      list_text : str
         A string representation of the list in dhcpd.conf syntax
      """

      # start of list
      list_text = ""
      list_text += "{}{} {{\n".format(self.__indent[list_indent], list_name)
      # list elements
      for list_item in list_items:
         list_text += "{}{}\n".format(self.__indent[item_indent],list_item)
      # end of list
      list_text += "{}}}\n".format(self.__indent[list_indent])
      return list_text

   def __dump_policies(self, policy_list, indent):
      """
      Dump a list of policies within a DHCP configuration in dhcpd.conf format.

      Parameters
      ----------
      policy_list : list of str
         List of policies.
      indent : int
         Indentation level to use for policies.

      Returns
      -------
      policy_text : str
         A string representation of the policies in dhcpd.conf syntax.
      """

      # start of policies
      policy_text = ""
      for policy in policy_list:
         policy_text += '{}policy {}'.format(self.__indent[indent],policy["policy_name"])
         # there might be multiple policy values
         policy_text += ' {}'.format(policy["policy_value"][0])
         for index in range(1,len(policy["policy_value"])):
            policy_text += ', {}'.format(policy["policy_value"][index])
         policy_text += ';\n'

      # done
      return policy_text

   def __dump_options(self, options_list, indent):
      """
      Dump a list of options within a DHCP configuration in dhcpd.conf format.

      Parameters
      ----------
      options_list : list of str
         List of options.
      indent : int
         Indentation level to use for options.

      Returns
      -------
      option_text : str
         A string representation of the options in dhcpd.conf syntax.
      """

      # start of options
      option_text = ""
      for option in options_list:
         option_text += '{}option {} {};\n'.format(self.__indent[indent],option["option_name"],option["option_value"])

      # done
      return option_text

   def __dump_client_class(self, client_class, indent, option_indent=0):
      """
      Dump a client class within a DHCP configuration in dhcpd.conf format.

      Parameters
      ----------
      client_class : dict
         A representation of the client class.
      indent : int
         Indentation level to use for the client class.

      Returns
      -------
      client_class_text = str
         A string representation of the client class in dhcpd.conf syntax.
      """

      if not option_indent:
         option_indent = indent + 1

      client_class_text = ""
      # vendor client class
      if client_class["class_type"] == "vendor-class":
         client_class_text += '{}{} "{}" {{\n'.format(self.__indent[indent],client_class["class_type"],client_class["class_match_value"])
      # user client class
      if client_class["class_type"] == "user-class":
         client_class_text += '{}{}'.format(self.__indent[indent],client_class["class_type"])
         for value in client_class["class_match_value"]:
            client_class_text += ' "{}"'.format(value)
         client_class_text += ' {\n'
      # option client class
      if client_class["class_type"] == "option-class":   
         client_class_text += '{}{} {} "{}" {{\n'.format(self.__indent[indent],client_class["class_type"],client_class["class_match_nr"],client_class["class_match_value"])
      # policies
      if self.__policies in client_class:
         client_class_text += self.__dump_policies(client_class[self.__policies],option_indent)
      # options
      if self.__options in client_class:
         client_class_text += self.__dump_options(client_class[self.__options],option_indent)
      # end of client class
      client_class_text += '{}}}\n'.format(self.__indent[indent])
      
      # done
      return client_class_text

   def __dump_subnet(self, subnet, indent):
      """
      Dump a subnet within a DHCP configuration in dhcpd.conf format.

      Params
      ------
      subnet : dict
         A representation of the subnet.
      indent : int
         The indention level to use for a subnet

      Returns
      -------
      subnet_text : str
         A string representation of the subnet in dhcpd.conf syntax
      """

      # start of subnet
      subnet_text = ""
      subnet_text += "{}subnet {} netmask {} {{\n".format(self.__indent[indent],subnet["subnet"],subnet["netmask"])

      # Excluded Fingerprints
      if self.__fingerprints in subnet:
         subnet_text += self.__dump_list(self.__fingerprints,subnet[self.__fingerprints ],indent+1,indent+2)

      # MAC Pools
      if self.__mac_pools in subnet:
         subnet_text += self.__dump_list(self.__mac_pools,subnet[self.__mac_pools],indent+1,indent+2)
      if self.__x_mac_pools in subnet:
         subnet_text += self.__dump_list(self.__x_mac_pools,subnet[self.__x_mac_pools],indent+1,indent+2)

      # ranges & fixed addresses
      if self.__ranges in subnet:
         for range_config in subnet[self.__ranges]:
            # range or fixed address?
            range_type = range_config["range_type"]
            fixed_addresses = [ 'manual-dhcp', 'manual-bootp' ]
            ranges = [ 'dynamic-dhcp', 'automatic-dhcp', 'automatic-bootp' ]
            if range_type in fixed_addresses:
               # start of fixed address
               subnet_text += '{}{} {} {}'.format(self.__indent[indent + 1],range_type,range_config["mac"],range_config["ip"])
            else:
               # start of range
               subnet_text += '{}{} range {} {}'.format(self.__indent[indent + 1],range_type,range_config["range_start"],range_config["range_end"])
               # vendor / user class filter
               if "vendor_class" in range_config:
                  subnet_text += ' class "{}"'.format(range_config["vendor_class"])
               if "user_class" in range_config:
                  subnet_text += ' userclass'
                  for user_class in range_config["user_class"]:
                     subnet_text += ' "{}"'.format(user_class)
            subnet_text += ' {\n'
            # range policies
            if self.__policies in range_config:
               subnet_text += self.__dump_policies(range_config[self.__policies], indent + 2)
            # range options
            if self.__options in range_config:
               subnet_text += self.__dump_options(range_config[self.__options], indent + 2)
            # range client classes
            if self.__client_classes in range_config:
               for client_class in range_config[self.__client_classes]:
                  subnet_text += self.__dump_client_class(client_class, indent + 2)
            # end of range
            subnet_text += '{}}}\n'.format(self.__indent[indent + 1])

      # sbubnet client class
      if self.__client_classes in subnet:
         for client_class in subnet[self.__client_classes]:
            subnet_text += self.__dump_client_class(client_class,indent + 1)

      # end of subnet
      subnet_text += "{}}}\n".format(self.__indent[indent])

      # done
      return subnet_text


   def dump(self, dhcpd_conf=None):
      """
      Dump a dhcpd conf dictionary back into a dhcpd.conf format.

      Params
      ------
      dhcpd_conf : dict
         A dictionary representing the dhcpd.conf, like the one returned by `get_config`.

      Returns
      -------
      dhcpd_conf_text : str
         A string representation of a dhcpd.conf file's content.
      """

      # if no config specified, use the current one
      if not dhcpd_conf:
         dhcpd_conf = self.__dhcpd_conf

      # start of file
      dhcpd_conf_text = ""
      dhcpd_conf_text += "server-identifier {};\n\n".format(dhcpd_conf["server-identifier"])
      indent_level = 1

      # fingerprints on top level
      if self.__fingerprints in dhcpd_conf:
         dhcpd_conf_text += self.__dump_list(self.__fingerprints, dhcpd_conf[self.__fingerprints], indent_level, indent_level + 2)

      # mac-pools on top level
      if self.__mac_pools in dhcpd_conf:
         dhcpd_conf_text += self.__dump_list(self.__mac_pools, dhcpd_conf[self.__mac_pools], indent_level, indent_level + 1)
         dhcpd_conf_text += "\n"

      # x-mac-pools on top level
      if self.__x_mac_pools in dhcpd_conf:
         dhcpd_conf_text += self.__dump_list(self.__x_mac_pools, dhcpd_conf[self.__x_mac_pools], indent_level, indent_level + 1)
         dhcpd_conf_text += "\n"

      # primary or failover configuration with multiple assigned primaries
      server_configurations = []
      if dhcpd_conf["is_failover"]:
         for primary in dhcpd_conf[self.__primary]:
            server_configurations.append(primary)
      else:
         server_configurations.append(dhcpd_conf)

      # dump rest of configuration
      for config in server_configurations:
         if "primary_server" in config:
            dhcpd_conf_text += "\nprimary-server {};\n\n".format(config["primary_server"])

         # print subnet
         if self.__subnets in config:
            for subnet in config[self.__subnets]:
               dhcpd_conf_text += self.__dump_subnet(subnet, 1)

         # shared_networks
         if self.__shared_networks in config:
            for shared_network in config[self.__shared_networks]:
               dhcpd_conf_text += "# Name: {}\n".format(shared_network["shared_network_name"])
               dhcpd_conf_text += "{}shared-network {} {{\n".format(self.__indent[0],shared_network["shared_network_id"])
               for subnet in shared_network[self.__subnets]:
                  dhcpd_conf_text += self.__dump_subnet(subnet, indent_level)
               dhcpd_conf_text += "{}}}\n".format(self.__indent[0])

         # client_classes
         if self.__client_classes in config:
            dhcpd_conf_text += "\n"
            for client_class in config[self.__client_classes]:
               dhcpd_conf_text += self.__dump_client_class(client_class, indent_level, option_indent=indent_level + 2)

      # done
      return dhcpd_conf_text

   def dump_to_file(self, dhcpd_conf_dir=None, file_name=None, backup_file_name=None, force=False):
      """
      Dump DHCP configuration to file if the `has_changed` attribute of dhcpd_conf or `force` is set to `True`

      Parameters
      ----------
      dhcpd_conf_dir : str, optional
         Directory that contains the DHCP configuration file (default: target_push_dir specified when creating DhcpdConf).
      file_name : str, optional
         Name of the DHCP configuration file (default: file_name specified when creating DhcpdConf).
      backup_file_name : str, optional
         Name of the DHCP configuration backup file (default: file_name plus ".orig").
      force : boolean, optional
         Enforce dump to file even if `has_changed` atrribute of dhcpd_pcy is `False`

      Returns
      -------
      int
         0 on success, > 0 if failure
      """

      # first check if something needs to be done at all
      dhcpd_conf = self.__dhcpd_conf
      if not dhcpd_conf["has_changed"] and not force:
         return 0

      # set up
      if not dhcpd_conf_dir:
         dhcpd_conf_dir = self.__dhcpd_conf_dir
      if not file_name:
         file_name = self.__file_name
      if not backup_file_name:
         backup_file_name = file_name + ".orig"
      dhcpd_conf_path = dhcpd_conf_dir + "/" + file_name
      dhcpd_conf_backup_path = dhcpd_conf_dir + "/" + backup_file_name

      # backup existing file before overwriting it
      if os.path.exists(dhcpd_conf_path):
         try:
            shutil.move(dhcpd_conf_path, dhcpd_conf_backup_path)
         except Exception as error:
            logger.exception("Failed to rename {} to {} : {} - {}".format(dhcpd_conf_path,dhcpd_conf_backup_path,type(error).__name__,error))
            return 10

      # create new dhcpd.conf based on dhcp_conf
      dhcpd_conf_text = self.dump()
      try:
         with open(dhcpd_conf_path, "w") as dhcpd_conf_fh:
            dhcpd_conf_fh.write(dhcpd_conf_text)
      except Exception as error:
         logger.exception("Failed to write {} : {} - {}".format(dhcpd_conf_path,type(error).__name__,error))
         return 20

   def dump_pcy(self, dhcpd_pcy=None):
      """
      Dump a dhcpd pcy dictionary back into a dhcpd.pcy format.

      Params
      ------
      dhcpd_pcy : dict
         A dictionary representing the dhcpd.pcy, like the one returned by `get_pcy`.

      Returns
      -------
      dhcpd_pcy_text : str
         A string representation of a dhcpd.pcy file's content.
      """

      # set up
      dhcpd_pcy_text = ""
      dhcpd_pcy_text += ";\n; QIP DHCP Policy File\n;\n"
      policies = self.__dhcpd_pcy["policies"]
      additional_policies = False

      # iterate through policies
      for policy in policies:
         # write start of Additional Policies only once
         if policy["additional_policy"] and not additional_policies:
            additional_policies = True
            dhcpd_pcy_text += "# Begin corporate extensions\n"
         # write policy
         dhcpd_pcy_text += "{}={}\n".format(policy["policy_name"],policy["policy_value"])
      # write end of Additional Policies
      if additional_policies:
         dhcpd_pcy_text += "; End corporate extensions\n"

      # done
      return dhcpd_pcy_text

   def dump_pcy_to_file(self, dhcpd_conf_dir=None, pcy_file_name=None, backup_file_name=None, force=False):
      """
      Dump DHCP policies to a file if the `has_changed` attribute of dhcpd_pcy or `force` is set to `True`

      Parameters
      ----------
      dhcpd_conf_dir : str, optional
         Directory that contains the DHCP configuration file (default: target_push_dir specified when creating DhcpdConf).
      pcy_file_name : str, optional
         Name of the DHCP policy file (default: pcy_file_name specified when creating DhcpdConf).
      backup_file_name : str, optional
         Name of the DHCP policy backup file (default: pcy_file_name plus ".orig").
      force : boolean, optional
         Enforce dump to file even if `has_changed` atrribute of dhcpd_pcy is `False`

      Returns
      -------
      int
         0 on success, > 0 if failure
      """

      # first check if something needs to be done at all
      dhcpd_pcy = self.__dhcpd_pcy
      if not dhcpd_pcy["has_changed"] and not force:
         return 0

      # set up
      if not dhcpd_conf_dir:
         dhcpd_conf_dir = self.__dhcpd_conf_dir
      if not pcy_file_name:
         pcy_file_name = self.__pcy_file_name
      if not backup_file_name:
         backup_file_name = pcy_file_name + ".orig"
      dhcpd_pcy_path = dhcpd_conf_dir + "/" + pcy_file_name
      dhcpd_pcy_backup_path = dhcpd_conf_dir + "/" + backup_file_name

      # backup existing file before overwriting it
      if os.path.exists(dhcpd_pcy_path):
         try:
            shutil.move(dhcpd_pcy_path, dhcpd_pcy_backup_path)
         except Exception as error:
            logger.exception("Failed to rename {} to {} : {} - {}".format(dhcpd_pcy_path,dhcpd_pcy_backup_path,type(error).__name__,error))
            return 10

      # create new dhcpd.pcy based on dhcp_pcy
      dhcpd_pcy_text = self.dump_pcy()
      try:
         with open(dhcpd_pcy_path, "w") as dhcpd_pcy_fh:
            dhcpd_pcy_fh.write(dhcpd_pcy_text)
      except Exception as error:
         logger.exception("Failed to write {} : {} - {}".format(dhcpd_pcy_path,type(error).__name__,error))
         return 20
         
class DomainHierarchy():
   """
   Represents DNS hierarchy and provides method to find best match in domain hierarchy
   """

   def __init__(self, domain_names):
      """
      Parameters
      ----------
      domain_names : list of str
         list of DNS zones/domains, no trailing dot.
         might contain root domain as "."
      """

      # created hashed list for quick lookup
      self.domain_list = {}
      for name in domain_names:
         self.domain_list[name] = 1

      # init domain hierarchy from list of domain names
      self.domain_hierarchy = {}
      for name in domain_names:
         labels = name.split(".")
         if not labels:
            continue
         hierarchy = self.domain_hierarchy
         # labels are sorted in reverse
         for label in labels[::-1]:
            if label not in hierarchy:
                  # create new hierarchy level
                  hierarchy[label] = {}
            # continue with next level in the hierarchy
            hierarchy = hierarchy[label]

   def get(self):
      """
      Return domain hierarchy
      """
      return self.domain_hierarchy

   def find(self, name):
      """
      Find closest matching domain name in hierarchy for a DNS name

      Parameters
      ----------
      name : str
         DNS Name without trailing dot

      Returns
      -------
      domain_name : str
         Closest matching domain name or empty string if domain name not in domain hierarchy
      """
      labels = name.split(".")
      hierarchy = self.domain_hierarchy
      domain_labels = []
      domain_name = ""
      # labels are sorted in reverse
      for label in labels[::-1]:
         if label in hierarchy:
            # continue with next level in the hierarchy
            hierarchy = hierarchy[label]
            # insert label into list of domain labels found
            domain_labels.insert(0, label)
         else:
            break

         # build domain name based on hierarchy labels found
         tmp_domain_name = ".".join(domain_labels)
         # determined domain must be in the domain list of known domains
         if tmp_domain_name in self.domain_list:
            domain_name = tmp_domain_name

      if domain_name == "":
         # special handling root zone
         if "." in self.domain_list:
            domain_name = "."

      return domain_name


###
### for testing
###
if __name__ == "__main__":
   print("Testing " + __file__)

   test_logger = 0
   test_run_command = 0
   test_named_conf = 0
   test_read_qip_pcy = 0
   test_dhcpd_conf = 1

   if test_logger:
      print("#####################################################################")
      print("TESTING Logger")
      print("#####################################################################")
   
      print("Creating logger #1 - logfile only")
      my_log_file = "/var/tmp/logfile.log"
      print("Using logfile " + my_log_file)
      try:
         logger1 = Logger(my_log_file)
      except Exception as error:
         print("logger #1 was not created: {0} - {1}".format(type(error).__name__,error))
      else:
         logger1.info("Info message after initializing")
         logger1.debug("Debug Message after initializing")
         logger1.trace("Trace Message after initializing")
   
         my_level = "TRACE"
         print("Setting logging level to " + my_level)
         error = logger1.set_level(my_level)
         if error:
            print("ERROR while setting logging level")
      
         logger1.info("Info message after setting log level")
         logger1.debug("Debug Message after setting log level")
         logger1.trace("Trace Message after setting log level")

         my_level = "STRACENEW"
         print("Setting logging level to " + my_level)
         error = logger1.set_level(my_level)
         if error:
            print("ERROR (expected) while setting logging level")
   
         my_size = "1M"
         my_no_of_backups = 3
         print("Enabling logfile rotation with size of " + my_size + " and " + str(my_no_of_backups) + " backups")
         error = logger1.enable_rotate_logging(my_size, my_no_of_backups)
         if error:
            print("ERROR while enabling log rotation")
      
         logger1.info("Info message after enabling log rotation")
         logger1.debug("Debug Message after enabling log rotation")
         logger1.trace("Trace Message after enabling log rotation")

         logger1.destroy()

      print()
      print("Creating logger #2 - console only")
      try:
         logger2 = Logger(console_logging = True)
      except Exception as error:
         print("logger #2 was not created: {0} - {1}".format(type(error).__name__,error))
      else:
         logger2.info("Info message after initializing")
         logger2.debug("Debug Message after initializing")
         logger2.trace("Trace Message after initializing")
   
         my_level = "TRACE"
         print("Setting logging level to " + my_level)
         error = logger2.set_level(my_level)
         if error:
            print("ERROR while setting logging level")
            exit()
      
         logger2.info("Info message after setting log level")
         logger2.debug("Debug Message after setting log level")
         logger2.trace("Trace Message after setting log level")
   
         my_size = "1M"
         my_no_of_backups = 3
         print("Enabling logfile rotation with size of " + my_size + " and " + str(my_no_of_backups) + " backups")
         error = logger2.enable_rotate_logging(my_size, my_no_of_backups)
         if error:
            print("ERROR (expected) while enabling debugging")

         logger2.destroy()

      print()
      print("Creating logger #3 - to logfile w/ overwrite and console logging, too")
      print("Using logfile " + my_log_file)
      try:
         logger3 = Logger(my_log_file, True, True)
      except Exception as error:
         print("logger #3 was not created: {0} - {1}".format(type(error).__name__,error))
      else:
         logger3.info("Info message after initializing")
         logger3.debug("Debug Message after initializing")
         logger3.trace("Trace Message after initializing")

         logger3.destroy()
         
   # allow logging for all other tests 
   logger = Logger(None, True)
   logger.set_level("TRACE")

   if test_run_command:
      print()
      print("#####################################################################")
      print("TESTING run_command")
      print("#####################################################################")
      command = "gibtsnicht"
      (error,stdout,stderr) = run_command(command)
      if error:
         print("ERROR (expected) while running command '" + command + "': " + stderr)

      command = "ls -l"
      (error,stdout,stderr) = run_command(command)
      if error:
         print("ERROR while running command '" + command + "': " + stderr)
      else:
         print("OUTPUT of command '" + command + "':\n" + stdout)

      command = "ls"
      command_args = [ "-l", "nnnn_toolkit.py" ]
      (error,stdout,stderr) = run_command(command, command_args)
      if error:
         print("ERROR while running command '" + command + "': " + stderr)
      else:
         print("OUTPUT of command '" + command + "':\n" + stdout)

      command = "ls -l %PASSWORD%"
      password = "topsecret"
      (error,stdout,stderr) = run_command(command, password=password)
      if error:
         print("ERROR while running command '" + command + "': " + stderr)
      else:
         print("OUTPUT of command '" + command + "':\n" + stdout)

      command = "ls"
      command_args = [ "-l", "%PASSWORD%" ]
      password = "anothersecret"
      (error,stdout,stderr) = run_command(command, command_args, password=password)
      if error:
         print("ERROR while running command '" + command + "': " + stderr)
      else:
         print("OUTPUT of command '" + command + "':\n" + stdout)

      command = "top -b -n 3"
      timeout_sec = 1;
      (error,stdout,stderr) = run_command(command, timeout=timeout_sec)
      if error:
         print("ERROR while running command '" + command + "': " + stderr)
      else:
         print("OUTPUT of command '" + command + "':\n" + stdout)

      command = "top -b -n 3"
      timeout_sec = 60;
      (error,stdout,stderr) = run_command(command, timeout=timeout_sec)
      if error:
         print("ERROR while running command '" + command + "': " + stderr)
      else:
         print("OUTPUT of command '" + command + "':\n" + stdout)

      command = "sleep 5"
      timeout_sec = 3;
      (error,stdout,stderr) = run_command(command, timeout=timeout_sec)
      if error:
         print("ERROR while running command '" + command + "': " + stderr)
      else:
         print("OUTPUT of command '" + command + "':\n" + stdout)

   if test_named_conf:
      print()
      print("#####################################################################")
      print("TESTING NamedConf")
      print("#####################################################################")
      my_named_conf_dir = '/opt/qip/current/named'
      named_conf = NamedConf(my_named_conf_dir)
      print("named.conf:\n" + named_conf.get_json())

      exit()

      view = "_vitalqip_global_namespace"
      zones = [ "tsig-secured.de", "dnssec.de", "static-zones.de", "0.0.127.in-addr.arpa", "168.192.in-addr.arpa"]
      for zone in zones:
         print("dynamic zone? checking zone " + zone + " in view " + view)
         if named_conf.is_dynamic(view, zone):
            print("it's a dynamic zone")
         else:
            print("it's is a static zone")

      zones = [ "newzone.de", "anotherzone" ]
      for zone in zones:
         print("notify = no? checking zone " + zone + " in view " + view)
         if named_conf.option_is_value(view, zone, "notify", "no"):
            print("notify = no")
         else:
            print("notify = yes")


   if test_read_qip_pcy:
      print()
      print("#####################################################################")
      print("TESTING read_qip_pcy")
      print("#####################################################################")
      qip_pcy = '/opt/qip/current/qip.pcy'
      try:
         (config, json_config) = read_qip_pcy(qip_pcy)
      except Exception as error:
         logger.error("failed to read/parse qip.pcy: {0} - {1}".format(type(error).__name__,error))
      else:
         print("Configuration as dict : {}".format(config))
         print("Configuration as JSON : {}".format(json_config))

   if test_dhcpd_conf:
      print()
      print("#####################################################################")
      print("TESTING DhcpdConf")
      print("#####################################################################")
      my_dhcpd_conf_path = '/opt/qip/current/dhcp'
      my_dhcpd_conf_file = 'dhcpd.conf'
      my_other_dhcpd_conf_file = 'dhcpd.conf.test'

      # read conf and print results
      dhcpd_conf = DhcpdConf(my_dhcpd_conf_path)
      logger.info("dhcpd conf from {} :\n{}".format(my_dhcpd_conf_file, dhcpd_conf.get_json()))
      logger.info("dhcpd pcy :\n{}".format(dhcpd_conf.get_json_pcy()))
      logger.info("dhcpd conf text : \n{}".format(dhcpd_conf.dump()))
      logger.info("dhcpd pcy text : \n{}".format(dhcpd_conf.dump_pcy()))

      # dump dhcpd.conf and dhcpd.pcy to disk
      error = dhcpd_conf.dump_to_file(file_name="dhcpd.conf.new", force=True)
      if error:
         logger.error("Failed to dump dhcpd.conf to a file")
      error = dhcpd_conf.dump_pcy_to_file(pcy_file_name="dhcpd.pcy.new", force=True)
      if error:
         logger.error("Failed to dump dhcpd.pcy to a file")

      # dhcpd.conf diff
      other_dhcpd_conf = DhcpdConf(my_dhcpd_conf_path, my_other_dhcpd_conf_file)
      logger.info("Differences between {} and {}:".format(my_dhcpd_conf_file,my_other_dhcpd_conf_file))
      diff_result = dhcpd_conf.diff(other_dhcpd_conf)
      for diff in diff_result:
         logger.info(diff)

