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
# Name:         nnnn_stackoverflow.py
# Company:      4N IT-Solutions GmbH
# Author:       Thomas Erhardt & Stackoverflow Contributors
# Date:         12.01.2022
#
# Description:  Various useful functions that have been copy & pasted
#               from Stackoverflow
#
# Requirements: The following non-default Python modules are required:
#               -
#
# Known issues: -
#
# Tested with:  -
#
#
# Changelog:
#  Date:        18.02.2022
#  Author:      Thomas Erhardt
#  Version:     1.0
#  Description: Initial Version
#
##########################################################################

# python doc
"""
Various useful functions that have been copy & pasted
from Stackoverflow
"""

# required modules
import logging
import configparser
import sys

# set up logging
logger = logging.getLogger("CommonLogger")
logger.setLevel(logging.INFO)

# this one taken from https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945,
# used by nnnn_toolkit for Logger class
def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present.

    (Note: taken from https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945)

    Parameters
    ----------
    levelName : str
      The name of the new level, e.g. TRACE.
    levelNum : int
      The numberic value of the new level, also see https://docs.python.org/3/howto/logging.html#logging-levels.
    methodName : str, optional
      The name of the method that will print messages of the new level.
      If not specified will be the name of the lever in lower case.

    Raises
    ------
    AttributeError
      If level name or method name already exist.

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} level already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} method already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)

# taken from https://stackoverflow.com/questions/13921323/handling-duplicate-keys-with-configparser
# with a slight modification to parse qip.pcy correctly,
# used by nnnn_toolkit in read_qip_pcy function
class ConfigParserMultiOpt(configparser.RawConfigParser):
  """
  ConfigParser allowing duplicate keys. Values are stored in a list.

  Note: Taken from https://stackoverflow.com/questions/13921323/handling-duplicate-keys-with-configparser
        with a slight modification to parse qip.pcy correctly.
  """

  def __init__(self):
    configparser.RawConfigParser.__init__(self, empty_lines_in_values=False, strict=False)

  def _read(self, fp, fpname):
    """
    Parse a sectioned configuration file.

    Each section in a configuration file contains a header, indicated by
    a name in square brackets (`[]'), plus key/value options, indicated by
    `name' and `value' delimited with a specific substring (`=' or `:' by
    default).

    Values can span multiple lines, as long as they are indented deeper
    than the first line of the value. Depending on the parser's mode, blank
    lines may be treated as parts of multiline values or ignored.

    Configuration files may include comments, prefixed by specific
    characters (`#' and `;' by default). Comments may appear on their own
    in an otherwise empty line or may be entered in lines holding values or
    section names.
    """
    elements_added = set()
    cursect = None                        # None, or a dictionary
    sectname = None

    # 4N mod - any value before the first section in [] will be treated as part of the DEFAULT section
    cursect = self._defaults

    optname = None
    lineno = 0
    indent_level = 0
    e = None                              # None, or an exception
    for lineno, line in enumerate(fp, start=1):
      comment_start = None
      # strip inline comments
      for prefix in self._inline_comment_prefixes:
        index = line.find(prefix)
        if index == 0 or (index > 0 and line[index-1].isspace()):
          comment_start = index
          break
      # strip full line comments
      for prefix in self._comment_prefixes:
        if line.strip().startswith(prefix):
          comment_start = 0
          break
      value = line[:comment_start].strip()
      if not value:
        if self._empty_lines_in_values:
          # add empty line to the value, but only if there was no
          # comment on the line
          if (comment_start is None and
              cursect is not None and
              optname and
              cursect[optname] is not None):
              cursect[optname].append('') # newlines added at join
        else:
          # empty line marks end of value
          indent_level = sys.maxsize
        continue
      # continuation line?
      first_nonspace = self.NONSPACECRE.search(line)
      cur_indent_level = first_nonspace.start() if first_nonspace else 0
      if (cursect is not None and optname and
          cur_indent_level > indent_level):
          cursect[optname].append(value)
      # a section header or option header?
      else:
        indent_level = cur_indent_level
        # is it a section header?
        mo = self.SECTCRE.match(value)
        if mo:
          sectname = mo.group('header')
          if sectname in self._sections:
            if self._strict and sectname in elements_added:
              raise DuplicateSectionError(sectname, fpname,
                                          lineno)
            cursect = self._sections[sectname]
            elements_added.add(sectname)
          elif sectname == self.default_section:
            cursect = self._defaults
          else:
            cursect = self._dict()
            self._sections[sectname] = cursect
            self._proxies[sectname] = configparser.SectionProxy(self, sectname)
            elements_added.add(sectname)
          # So sections can't start with a continuation line
          optname = None
        # no section header in the file?
        elif cursect is None:
          raise MissingSectionHeaderError(fpname, lineno, line)
        # an option line?
        else:
          mo = self._optcre.match(value)
          if mo:
            optname, vi, optval = mo.group('option', 'vi', 'value')
            if not optname:
              e = self._handle_error(e, fpname, lineno, line)
            optname = self.optionxform(optname.rstrip())
            if (self._strict and
              (sectname, optname) in elements_added):
              raise configparser.DuplicateOptionError(sectname, optname, fpname, lineno)
            elements_added.add((sectname, optname))
            # This check is fine because the OPTCRE cannot
            # match if it would set optval to None
            if optval is not None:
              optval = optval.strip()
              # Check if this optname already exists
              if (optname in cursect) and (cursect[optname] is not None):
                # If it does, convert it to a tuple if it isn't already one
                if not isinstance(cursect[optname], tuple):
                  cursect[optname] = tuple(cursect[optname])
                cursect[optname] = cursect[optname] + tuple([optval])
              else:
                cursect[optname] = [optval]
            else:
                # valueless option handling
                cursect[optname] = None
          else:
            # a non-fatal parsing error occurred. set up the
            # exception but keep going. the exception will be
            # raised at the end of the file and will contain a
            # list of all bogus lines
            e = self._handle_error(e, fpname, lineno, line)
    # if any parsing errors occurred, raise an exception
    if e:
        raise e
    self._join_multiline_values()



