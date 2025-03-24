 #!/usr/bin/python3.9

##########################################################################
#  _  _   _   _   ___ _____    ____        _       _   _                 
# | || | | \ | | |_ _|_   _|  / ___|  ___ | |_   _| |_(_) ___  _ __  ___ 
# | || |_|  \| |  | |  | |____\___ \ / _ \| | | | | __| |/ _ \| '_ \/ __|
# |__   _| |\  |  | |  | |_____|__) | (_) | | |_| | |_| | (_) | | | \__ \
#    |_| |_| \_| |___| |_|    |____/ \___/|_|\__,_|\__|_|\___/|_| |_|___/
#
##########################################################################
#
# Name:         dhcp-probe.py
# Company:      4N IT-Solutions GmbH
# Author:       Thomas Erhardt
# Date:         14.11.2022
#
# Description:  DHCP Probe to check DHCP responses from specific / all servers
#
# Requirements: Python version must be 3.8 or newer (i.e. Python 3.9 on Rocky Linux)
#               The following non-default Python modules are required:
#               nnnn_toolkit
#               dhcppython (can only be installed via pip3.9)
#
# Known issues: -
#
# Tested with:  VitalQIP 21 on Rocky Linux 8.6
# 
##########################################################################


# dependencies : will be checked by installation script
# DEPENDS_ON_MODULE: json,python3-libs
# DEPENDS_ON_MODULE: dhcppython,pip3.9-install-dhcppython
# DEPENDS_ON: python39-pip

# python doc
"""
DHCP Probe to check DHCP responses from specific / all servers. Sends a DHCP package and displays the received response(s).

Usage:
dhcp-probe.py [-t <test>] [-m <MAC Address>] [-H <hostname>] [-b] [-v <vendor class>] [-u <user class>] [-f <fqdn>] [-F <fqdn flags>] [-c <client ID>|-C <hex client ID>] [-o <opcode=string value>] [-O <opcode=hex value>] [-p <parameter request list>] [-r <requested IP>] [-s <server IP>] [-R <relay IP>] [-a <accepted server IP>] [-A] [-P] [-i <interface name>] [-d]

   -t <test>:     determine the type of DHCP test that will be done, valid values are
                  discover-only (default): only send DISCOVER (broadcast) to see which DHCP Servers respond
                  request-only: only send REQUEST (default: broadcast) to confirm lease, requires "-r <requested IP>",
                                can be used with "-s <server>" to unicast a DHCP request.
                  release-only: only send RELEASE (unicast), requires "-r <requested IP>" and "-s <server>"
                  dora: go through DISCOVER/OFFER/REQUEST/ACK cycle (uses broadcasts)
                  full-cycle: go through DISCOVER/OFFER/REQUEST/ACK (broadcast), REQUEST (unicast), RELEASE (unicast) cycle

   -m <MAC Address>:    MAC Address to use in format abcdef123456 (separators :, - or . are allowed), defaults to 4e:4e:4e:4e:00:00

   -H <hostname>:       The hostname/option 12 value (unqualified) to use, defaults to 4n-dhcp-probe

   -b:                  If set the broadcast flag will be set in outgoing packets

   -v <vendor class>:   The vendor class/option 60 value to use (string)

   -u <user class>:     The user class/option 77 value to use (string)

   -f <fqdn>:           The FQDN to use within Option 81 (string)

   -F <fqdn flags>:     The Flags to set within Option 81, can be N or S. Defaults to flags being not set.

   -c <client ID>:      The client id/option 61 value to use (string), mutually exclusive with "-C <hex client ID>"

   -C <hex client ID>:  The client id/option 61 value to use (byte string), mutually exclusive with "-c <client ID>",
                        can optionally use ":" to separate bytes

   -o <opcode=string>:  Specify additional option <opcode> for that no convenience command line switch exists,
                        value must be a text/string, can be repeated multiple times to specify multiple options.

   -O <opcode=hex>:     Specify additional option <opcode> for that no convenience command line switch exists,
                        value must be a byte string (hex), can optionally use ":" to separate bytes, can be 
                        repeated multiple times to specify multiple options.

   -p <parameter request list>:  The parameter request list/option 55 value, is specified as a comma separated
                        list of decimal option numbers.

   -r <requested IP>:   Specify the requested IPv4 address/option 50 value. Is required when using "-t request-only".
                        Can be INIT-REBOOT (broadcast) or RENEWING state (unicast) when using "-s <server IP>".

   -s <server IP>:      Specify DHCP Server IP address to use for unicasts.

   -R <relay IP>:       IP Address of the DHCP Relay to use as giaddr value (unicast), requires "-s <server IP>"

   -a <accepted server IP>: Specify a DHCP Server IP to accept a response from. Can be repeated multiple times. If 
                        other servers do respond their response will be ignored and will not be displayed. 

   -A:                  Enforce accepted servers. Requires "-a <accepted server IP>". When specified will display responses 
                        from servers other than the accepted ones as error and exit with an error code = 1.

   -P:                  Primary mode. Requires "-a <accepted server IP>". If multiple accepted servers are specified treat 
                        response from other server than first in the list as problem and exit with error code = 2.

   -i <interface name>: Specify the name  of the interface for DHCP testing, might be required if test system is multihomed.

   -M:                  Automatically probe the local DHCP service.

   -d:                  Enable debugging output. Specify multile times to get more details (max 3 times).
"""

# required modules
import json
import re
import os
import argparse
#import time
import socket
import ipaddress
import random
import psutil
# required for binary build
from sys import exit

# required non-standard modules
import nnnn_toolkit as toolkit
import dhcppython

# set up error codes
error_code_base = 10000
exit_code_warning = 1
exit_code_error = 2

# helpers
def setup_socket(ip_and_port, if_name, receive_timeout):
   dhcp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   dhcp_socket.settimeout(receive_timeout)
   
   try:
      if args.interface:
         dhcp_socket.setsockopt(socket.SOL_SOCKET, 25, bytes(args.interface, 'ascii'))
   except OSError as e:
      logger.error("Setting up socket on interface '{}' failed : {}".format(if_name, e))
      exit(exit_code_error)

   try:
      dhcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
   except OSError as e:
      logger.error("Setting up socket for broadcasts failed : {}".format(if_name, e))
      exit(exit_code_error)

   try:
      dhcp_socket.bind(ip_and_port)
   except OSError as e:
      logger.error("Setting up socket on '{}' failed: {}".format(ip_and_port, e))
      exit(exit_code_error)

   return dhcp_socket

def shutdown_socket(dhcp_socket):
   try:
      dhcp_socket.close()
   except OSError as e:
      logger.error("Closing socket failed: {}".format(e))
      exit(exit_code_error)

def send_query(dhcp_socket, dhcp_packet, dhcp_server):
   try:
      dhcp_socket.sendto(dhcp_packet.asbytes, dhcp_server)
   except Exception as e:
      logger.error("Error while sending to DHCP Server {}: {} - {}".format(dhcp_server, type(e).__name__,e))
      exit(exit_code_error)
   return dhcp_packet

def receive_response(dhcp_socket):
   try:
      (response, sender) = dhcp_socket.recvfrom(receive_package_size)
   except Exception as e:
      if type(e).__name__ != "timeout":
         logger.error("Error while waiting for DHCP Server response: {} - {}".format(type(e).__name__,e))
         exit(exit_code_error)
      return None
   dhcp_response = dhcppython.packet.DHCPPacket.from_bytes(response)
   return dhcp_response

def print_dhcp_packet(dhcp_packet):
   header = {
      "hops": dhcp_packet.hops,
      "secs": dhcp_packet.secs,
      "flags": dhcp_packet.flags,
      "ciAddr": dhcp_packet.ciaddr,
      "yiAddr": dhcp_packet.yiaddr,
      "siAddr": dhcp_packet.siaddr,
      "giAddr": dhcp_packet.siaddr,
      "chAddr": dhcp_packet.chaddr,
      "sName": dhcp_packet.sname,
      "bootFile": dhcp_packet.file
   }
   logger.debug(" Header:")
   for field in header:
      logger.debug(" {} : {}".format(field, header[field]))
   logger.debug(" Options:")
   for option in dhcp_packet.options:
      logger.debug("  {}".format(option.value))

def dhcp_type(dhcp_packet):
   message_type_value = dhcp_packet.options.by_code(53)
   value_to_type = {
      b"\x01": "DHCPDISCOVER",
      b"\x02": "DHCPOFFER",
      b"\x03": "DHCPREQUEST",
      b"\x04": "DHCPDECLINE",
      b"\x05": "DHCPACK",
      b"\x06": "DHCPNAK",
      b"\x07": "DHCPRELEASE",
      b"\x08": "DHCPINFORM"
   }
   return value_to_type[message_type_value.data]

def dhcp_server_id(dhcp_packet):
   server_id_value = dhcp_packet.options.by_code(54)
   ip_address = ipaddress.IPv4Address(server_id_value.data)
   return ip_address

def add_ip(if_name, ip):
   cmd = "ip address add {}/32 dev {}".format(ip, if_name)
   logger.debug("Adding IP {} to interface {}".format(ip, if_name))
   (error, stdout, stderr) = toolkit.run_command(cmd)
   if error:
      raise OSError("Failed to add IP {} to {} using '{}' : {}".format(ip, if_name, cmd, stderr))
   return ip

def delete_ip(if_name, ip):
   cmd = "ip address delete {}/32 dev {}".format(ip, if_name)
   logger.debug("Removing IP {} from interface {}".format(ip, if_name))
   (error, stdout, stderr) = toolkit.run_command(cmd)
   if error:
      raise OSError("Failed to delete IP {} from {} using '{}' : {}".format(ip, if_name, cmd, stderr))

def get_ipv4_networks():
   localnets = {}
   network_config = psutil.net_if_addrs()
   for interface in network_config:
      for snic in network_config[interface]:
         if snic.family != socket.AF_INET:
            continue
         if snic.address == "127.0.0.1":
            continue
         network = ipaddress.IPv4Network("{}/{}".format(snic.address,snic.netmask), strict=False)
         if interface not in localnets:
            localnets[interface] = []
         localnets[interface].append(network)
   return localnets

def check_accepted_server(ip, accepted_servers):
   if accepted_servers:
      if ip in accepted_servers:
         return True
      else:
         return False
   else:
      return True

# defaults for configuration file settings
config = {
   # where to check for dhcpd.conf
   "dhcpd_conf_dir": "/opt/qip/current/dhcp",

   # path to log file
   "log_file": "/opt/qip/current/log/dhcp-probe.log",

   # timeout (in seconds)
   "dhcp_timeout": 3,

   # number of retries
   "dhcp_attempts": 3
}

# override defaults based on environment
if "QDHCPCONFIG" in os.environ:
   config["dhcpd_conf_dir"] = os.environ["QDHCPCONFIG"]
if "QIPHOME" in os.environ:
   config["log_file"] = os.path.join(os.environ["QIPHOME"],"log","dhcp-probe.log")

# read config file if present
script_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(script_dir, "dhcp-probe.conf")
if os.path.exists(config_file):
   config, config_json = toolkit.read_config(config_file, config)

# initialize logging
logger = toolkit.Logger(log_file = config["log_file"], console_logging = True)
logger.set_level("INFO")

error_cnt = 0
debug = 0

arg_parser = argparse.ArgumentParser(description='4N DHCP-Probe', allow_abbrev=False, add_help=True)
arg_parser.add_argument('-t', '--test', choices=['discover-only', 'request-only', 'release-only', 'dora', 'full-cycle'], default='discover-only', help="Test mode to use")
arg_parser.add_argument('-m', '--mac-address', default='4e:4e:4e:4e:00:00', help="MAC address to use. Format is 11:22:33:aa:bb:cc, 44-55-66-dd-ee-ff or 123456abcdef")
arg_parser.add_argument('-H', '--hostname', default='4n-dhcp-probe', help="Hostname to use")
arg_parser.add_argument('-b', '--broadcast', action='store_true', help="Set Broadcast Flag")
arg_parser.add_argument('-v', '--vendor-class', help="Vendor Class to use")
arg_parser.add_argument('-u', '--user-class', help="User Class to use")
arg_parser.add_argument('-f', '--fqdn', help="FQDN for Option 81 to use (WIP)")
arg_parser.add_argument('-F', '--fqdn-flags', choices=['N', 'S'], help="Flags for Option 81 to set (WIP)")
arg_parser.add_argument('-c', '--client-id', help="Client ID to use (string)")
arg_parser.add_argument('-C', '--client-id-hex', help="Client ID to use (hex numbers colon separated)")
arg_parser.add_argument('-o', '--option', action='append', help="Additional option to send (string)")
arg_parser.add_argument('-O', '--option-hex', action='append', help="Additional option to send (hex numbers colon separated)")
arg_parser.add_argument('-p', '--parameter-request-list', help="Parameter Request List to send (comma separated)")
arg_parser.add_argument('-r', '--requested-ip-address', help="Requested IP Address to send")
arg_parser.add_argument('-s', '--server-ip', help="Server IP Address (for unicasts)")
arg_parser.add_argument('-R', '--relay-ip', help="Fake DHCP Relay IP Address (giaddr) (for unicasts)")
arg_parser.add_argument('-a', '--accepted-server', action='append', help="Use these server's reponses only")
arg_parser.add_argument('-A', '--accepted-server-only', action='store_true', help="Enforce answers from accepted servers only (WIP)")
arg_parser.add_argument('-P', '--primary', action='store_true', help="Enforce answers from primary accepted servers only (WIP)")
arg_parser.add_argument('-i', '--interface', help="Interface to use for sending/receiving packets")
arg_parser.add_argument('-M', '--monitoring', action='store_true', help="Automatically probe the local DHCP service")
arg_parser.add_argument('-d', '--debug', action='count', help="Enable debugging, can be specified up to two times to increase level of details")
args = arg_parser.parse_args()

# handle command line args
args_error = False
monitoring = False

# set up debugging
if args.debug:
   debug = args.debug
   logger.set_level("DEBUG")
   if debug > 2:
      logger.set_level("TRACE")

# format / check command line args
match = re.search("^([a-fA-F0-9]{2}[:\-]?){5}[a-fA-F0-9]{2}$", args.mac_address)
if not match:
   logger.error("Invalid MAC address '{}', required format is 11:22:33:aa:bb:cc, 44-55-66-dd-ee-ff or 123456abcdef".format(args.mac_address))
   args_error = True
args.mac_address = re.sub("^([0-9a-fA-F]{2})([:\-]?)([0-9a-fA-F]{2})([:\-]?)([0-9a-fA-F]{2})([:\-]?)([0-9a-fA-F]{2})([:\-]?)([0-9a-fA-F]{2})([:\-]?)([0-9a-fA-F]{2})$", r"\1:\3:\5:\7:\9:\11", args.mac_address)

if args.client_id_hex:
   client_id_hex = re.sub(":", "", args.client_id_hex)
   match = re.search("([^a-fA-F0-9])", client_id_hex)
   if match:
      invalid_chars = match.group(1)
      logger.error("Invalid character '{}' in specified Client ID (hex) '{}'".format(invalid_chars, args.client_id_hex))
      args_error = True

option_list = {}
if args.option:
   for option in args.option:
      try:
         (op_code, op_value) = option.split("=")
         option_list[op_code] = op_value
      except ValueError:
         logger.error("incorrectly formatted option '{}', format is op_code=op_value, e.g. '77=test'".format(option))
         args_error = True

option_list_hex = {}
if args.option_hex:
   for option in args.option_hex:
      try:
         (op_code, op_value) = option.split("=")
         new_op_value = re.sub(":", "", op_value)
         match = re.search("([^a-fA-F0-9])", new_op_value)
         if match:
            invalid_chars = match.group(1)
            logger.error("Invalid character '{}' in specified Option {} value '{}'".format(invalid_chars, op_code, op_value))
            args_error = True
         else:
            option_list_hex[op_code] = new_op_value
      except ValueError:
         logger.error("incorrectly formatted option '{}', format is op_code=hex_op_value, e.g. '77=74:65:73:74'".format(option))
         args_error = True

if args.parameter_request_list:
   match = re.search("^[1-9][0-9,]*$", args.parameter_request_list)
   if not match:
      logger.error("Invalid parameter request list '{}', need decimal numbers separated by comme, e.g. '1,3,15'".format(args.parameter_request_list))
      args_error = True

# check IPs
if args.requested_ip_address:
   try:
      requested_ip_address = ipaddress.IPv4Address(args.requested_ip_address)
   except ipaddress.AddressValueError:
      logger.error("specified requested IP address '{}' is not a valid IPv4 Addresss".format(args.requested_ip_address))
      args_error = True

if args.server_ip:
   try:
      server_ip = ipaddress.IPv4Address(args.server_ip)
   except ipaddress.AddressValueError:
      logger.error("specified server IP address '{}' is not a valid IPv4 Addresss".format(args.server_ip))
      args_error = True

accepted_servers = []
if args.accepted_server:
   for ip_address in args.accepted_server:
      try:
         ip = ipaddress.IPv4Address(ip_address)
         accepted_servers.append(ip)
      except ipaddress.AddressValueError:
         logger.error("specified accepted server IP address '{}' is not a valid IPv4 Addresss".format(ip_address))
         args_error = True

# check conflicting options
if args.client_id and args.client_id_hex:
   logger.error("Parameters -c and -C are mutually exclusive - specify only one of them")
   args_error = True

# check required options
if args.test == "request-only":
   if not args.requested_ip_address:
      logger.error("Test 'request-only' requires option '-r <requested IP Address>'")
      args_error = True

if args.test == "release-only":
   if not args.requested_ip_address:
      logger.error("Test 'request-only' requires option '-r <requested IP Address>'")
      args_error = True
   if not args.server_ip:
      logger.error("Test 'request-only' requires option '-s <server IP>'")
      args_error = True

if args.accepted_server_only or args.primary:
   if not args.accepted_server:
      logger.error("Options -A and -P require at lease one accepted server with '-a <accepted server IP>'")
      args_error = True

if args.relay_ip:
   if not args.server_ip:
      logger.error("Option -R requires option '-s <server IP>'")
      args_error = True

if args.monitoring:
   monitoring = True

# exit on error
if args_error:
   exit(exit_code_error)

# info on probe config used
logger.trace("Using configuration:\n" + config_json)

# automated monitoring of local DHCP Server only
if monitoring:
   if not toolkit.is_running("dhcpd"):
      logger.warning("DHCP Server is not running, exiting DHCP Probe")
      exit(exit_code_warning)

   logger.info("Reading dhcpd.conf")
   try:
      dhcpd_conf = toolkit.DhcpdConf(config["dhcpd_conf_dir"])
   except Exception as error:
      logger.error("Failed to parse dhcpd.conf in {} : {} - {}".format(config["dhcpd_conf_dir"],type(error).__name__,error))
      exit(exit_code_error)
   logger.info("Reading dhcpd.conf completed")

   # make sure ListenOnLoopback=1
   dhcpd_pcy = dhcpd_conf.get_pcy()
   listen_on_loopback = False
   for policy in dhcpd_pcy["policies"]:
      if re.search("ListenOnLoopback", policy["policy_name"], re.IGNORECASE):
         if policy["policy_value"] == "1":
            listen_on_loopback = True
         break
   if not listen_on_loopback:
      logger.error("Need policy ListenOnLoopback=1 in dhcpd.pcy / Additional Policies")
      exit(exit_code_error)

   # get locally attached IPv4 subnets to check if they exist in the configuration
   localnets = []
   interface_nets = get_ipv4_networks()
   for interface in interface_nets:
      for localnet in interface_nets[interface]:
         localnets.append(localnet)

   # determine IP / MAC adddress to use (requires M-DHCP to be configured in local subnet)
   found = False
   relay_ip = None
   mac_address = None
   dhcpd_config = dhcpd_conf.get_config()
   for subnet in dhcpd_config["subnets"]:
      for localnet in localnets:
         if subnet["subnet"] == str(localnet.network_address) and subnet["netmask"] == str(localnet.netmask):
            ranges = subnet["ranges"]
            for dhcp_range in ranges:
               if dhcp_range["range_type"] == "manual-dhcp":
                  mac = dhcp_range["mac"]
                  if re.search("^4e-4e-4e-4e", mac):
                     mac_address = re.sub("-", ":", mac)
                     relay_ip = dhcp_range["ip"]
                     found = True
                     break
         if found:
            break            
      if found:
         break
   if not found:
      logger.error("Need M-DHCP with MAC 4e:4e:4e:4e:xx:xx in a local subnet: {}".format(localnets))
      exit(exit_code_error)
   logger.debug("Using Relay IP {} and MAC {} for DHCP Probe".format(relay_ip, mac_address))

   # override command line args
   args.interface = "lo"
   args.server_ip = "127.0.0.1"
   args.relay_ip = relay_ip
   args.mac_address = mac_address
   

# track ip configuration
tmp_ip = None

# set up DHCP sockets
dhcp_server = ("255.255.255.255", 67)
if args.server_ip:
   dhcp_server = (args.server_ip, 67)

dhcp_client = ("0.0.0.0", 68)
if args.relay_ip:
   dhcp_client = ("0.0.0.0", 67)
   if args.interface:
      dhcp_client = (args.relay_ip, 67)
      tmp_ip = add_ip(args.interface, args.relay_ip)
   else:
      logger.warn("Specify '-i <interface>' to receive unicast responses to {}".format(args.relay_ip))

logger.debug("Using MAC {}".format(args.mac_address))
logger.debug("Waiting for response on {}".format(dhcp_client))
dhcp_socket = setup_socket(dhcp_client, args.interface, config["dhcp_timeout"])

receive_package_size = 2048


# build option list
options = dhcppython.options.OptionList()

# simple options
options.append(dhcppython.options.options.short_value_to_object(12, args.hostname))
if args.vendor_class:
   options.append(dhcppython.options.options.short_value_to_object(60, args.vendor_class))
if args.user_class:
   byte_value = bytes(args.user_class, encoding="utf-8")
   options.append(dhcppython.options.UnknownOption(77, len(byte_value), byte_value))
if args.client_id:
   options.append(dhcppython.options.options.short_value_to_object(61, args.client_id))

# other options
if args.parameter_request_list:
   requested_options = ""
   for option in args.parameter_request_list.split(","):
      requested_options += "{:02x}".format(int(option))
   options.append(dhcppython.options.options.short_value_to_object(55, bytes.fromhex(requested_options)))

# regular options
for op_code in option_list:
   value = option_list[op_code]
   byte_value = bytes(value, encoding="utf-8")
   options.append(dhcppython.options.UnknownOption(int(op_code), len(byte_value), byte_value))

# hex options
for op_code in option_list_hex:
   value = option_list_hex[op_code]
   byte_value = bytes.fromhex(value)
   options.append(dhcppython.options.UnknownOption(int(op_code), len(byte_value), byte_value))

# init packets to be sent/received
dhcp_discover = None
dhcp_request = None
dhcp_response = None

# run tests

## Send DHCPDISCOVER
## discover-only will wait for multiple DHCPOFFERs
## dora/full-cycle will use the first matching DHCPOFFER (xid) to continue
if args.test == "discover-only" or args.test == "dora" or args.test == "full-cycle":
   # build DISCOVER and send it
   dhcp_discover = dhcppython.packet.DHCPPacket.Discover(mac_addr = args.mac_address, use_broadcast = args.broadcast, relay = args.relay_ip, option_list = options)
   logger.trace("Sending DHCPDISCOVER: {}".format(dhcp_discover))
   logger.info("Sending DHCPDISCOVER to {}".format(dhcp_server))
   dhcp_discover = send_query(dhcp_socket, dhcp_discover, dhcp_server)
   if debug > 1:
      print_dhcp_packet(dhcp_discover)

   # collect responses
   response_received = False
   while True:
      dhcp_response = receive_response(dhcp_socket)
      if not dhcp_response:
         # timeout while waiting for response
         break
      else:
         # received some response
         if dhcp_response.xid == dhcp_discover.xid:
            logger.trace("Got response: {}".format(dhcp_response))
            message_type = dhcp_type(dhcp_response)
            server_id = dhcp_server_id(dhcp_response)
            if not check_accepted_server(server_id, accepted_servers):
                logger.warn("Ignoring response ({}) from {}".format(message_type, server_id))
                continue
            logger.debug("Got response ({}) from {}".format(message_type, server_id))
            if message_type == "DHCPOFFER":
               logger.info("Received DHCPOFFER for IP {} from {}".format(dhcp_response.yiaddr,server_id))
               print_dhcp_packet(dhcp_response)
               response_received = True
               if args.test == "dora" or args.test == "full-cycle":
                  # one response is sufficent
                  break
         else:
            logger.info("Ignoring response for a different xid")
   
   if not response_received:
      logger.error("Did not receive any response")
      error_cnt += 1


## Send DHCPREQUEST as part of DORA
if (args.test == "dora" or args.test == "full-cycle") and not error_cnt:
   # add yiAddr from resonse as requested IP
   options.append(dhcppython.options.options.short_value_to_object(50, dhcp_response.yiaddr))
   # add server identifier option from resonse
   options.append(dhcp_response.options.by_code(54))
   
   # build DHCPREQUEST & send it
   dhcp_request = dhcppython.packet.DHCPPacket.Request(mac_addr = args.mac_address, use_broadcast = args.broadcast, relay = args.relay_ip, tx_id = dhcp_discover.xid, seconds = 0, option_list = options)
   logger.trace("Sending DHCPREQUEST: {}".format(dhcp_request))
   logger.info("Sending DHCPREQUEST to {}".format(dhcp_server))
   dhcp_request = send_query(dhcp_socket, dhcp_request, dhcp_server)
   if debug > 1:
      print_dhcp_packet(dhcp_request)

   # collect responses
   response_received = False
   while True:
      dhcp_response = receive_response(dhcp_socket)
      if not dhcp_response:
         # timeout while waiting for response
         break
      else:
         # received some response
         if dhcp_response.xid == dhcp_discover.xid:
            logger.trace("Got response: {}".format(dhcp_response))
            message_type = dhcp_type(dhcp_response)
            server_id = dhcp_server_id(dhcp_response)
            if not check_accepted_server(server_id, accepted_servers):
                logger.warn("Ignoring response ({}) from {}".format(message_type, server_id))
                continue
            logger.debug("Got response ({}) from {}".format(message_type, server_id))
            if message_type == "DHCPACK" or message_type == "DHCPNAK":
               logger.info("Received {} for IP {} from {}".format(message_type,dhcp_response.yiaddr,server_id))
               print_dhcp_packet(dhcp_response)
               response_received = True
               break
         else:
            logger.info("Ignoring response for a different xid (my xid : {}, received xid : {}", dhcp_discover.xid, dhcp_response.xid)
   
   if not response_received:
      logger.error("Did not receive any response")
      error_cnt += 1

## Send DHCPREQUEST to renew IP Address (INIT-REBOOT, RENEWING)
if (args.test == "request-only" or (dhcp_response and args.test == "full-cycle")) and not error_cnt:
   if not args.interface:
      logger.warn("Specify '-i <interface>' to receive unicast responses to {}".format(dhcp_request.ciaddr))

   # this is required for request-only
   if not dhcp_discover:
      dhcp_discover = dhcppython.packet.DHCPPacket.Discover(mac_addr = args.mac_address, use_broadcast = args.broadcast, relay = args.relay_ip, option_list = options)

   # build DHCPREQUEST
   dhcp_request = dhcppython.packet.DHCPPacket.Request(mac_addr = args.mac_address, use_broadcast = args.broadcast, relay = args.relay_ip, tx_id = dhcp_discover.xid, seconds = 0, option_list = options)

   # track if using unicasts
   unicast = False

   # for full-cycle : use values from previous response
   if dhcp_response:
      unicast = True
      # use yiAddr from response as ciAddr
      dhcp_request.ciaddr = dhcp_response.yiaddr
      # add yiAddr from resonse as requested IP
      options.append(dhcppython.options.options.short_value_to_object(50, dhcp_response.yiaddr))
      # add server identifier option from resonse
      options.append(dhcp_response.options.by_code(54))
      # use unicast to renew IP address
      server_id = dhcp_server_id(dhcp_response)
      dhcp_server = ("{}".format(server_id), 67)
   # for request-only: use values from command line
   else:
      options.append(dhcppython.options.options.short_value_to_object(50, args.requested_ip_address))

   # init-boot (broadcast) vs. renew (unicast)
   if args.test == "request-only":
      if args.server_ip:
         unicast = True
         logger.info("Renewing IP {} (unicast/RENEWING)".format(args.requested_ip_address))
         options.append(dhcppython.options.options.short_value_to_object(54, args.server_ip))
         dhcp_server = (args.server_ip, 67)
         dhcp_request.ciaddr = ipaddress.IPv4Address(args.requested_ip_address)
      else:
         logger.info("Renewing IP {} (broadcast/INIT-REBOOT)".format(args.requested_ip_address))

   if unicast:
      # assign ciaddr so responses are actually received
      if args.interface:
         if not args.relay_ip:
            tmp_ip = add_ip(args.interface, dhcp_request.ciaddr)
            dhcp_client = ("{}".format(dhcp_request.ciaddr), 68)
            try:
               shutdown_socket(dhcp_socket)
               dhcp_socket = setup_socket(dhcp_client, args.interface, config["dhcp_timeout"])
            except OSError as e:
               logger.error("Setting up socket on '{}' failed: {}".format(dhcp_client, e))
               delete_ip(args.interface, tmp_ip)
               exit(exit_code_error)

   # send DHCPREQUEST
   logger.trace("Sending DHCPREQUEST: {}".format(dhcp_request))
   logger.info("Sending DHCPREQUEST to {}".format(dhcp_server))
   dhcp_request = send_query(dhcp_socket, dhcp_request, dhcp_server)
   if debug > 1:
      print_dhcp_packet(dhcp_request)

   # collect responses
   response_received = False
   while True:
      dhcp_response = receive_response(dhcp_socket)
      if not dhcp_response:
         # timeout while waiting for response
         break
      else:
         # received some response
         if dhcp_response.xid == dhcp_discover.xid:
            logger.trace("Got response: {}".format(dhcp_response))
            message_type = dhcp_type(dhcp_response)
            server_id = dhcp_server_id(dhcp_response)
            if not check_accepted_server(server_id, accepted_servers):
                logger.warn("Ignoring response ({}) from {}".format(message_type, server_id))
                continue
            logger.debug("Got response ({}) from {}".format(message_type, server_id))
            if message_type == "DHCPACK" or message_type == "DHCPNAK":
               logger.info("Received {} for IP {} from {}".format(message_type,dhcp_response.yiaddr,server_id))
               print_dhcp_packet(dhcp_response)
               response_received = True
               break
         else:
            logger.info("Ignoring response for a different xid (my xid : {}, received xid : {}", dhcp_discover.xid, dhcp_response.xid)
   
   if not response_received:
      logger.error("Did not receive any response")
      error_cnt += 1

## Send DHCPRELEASE
if (args.test == "release-only" or args.test == "full-cycle") and not error_cnt:
   options.append(dhcppython.options.options.short_value_to_object(53, "DHCPRELEASE"))
   dhcp_release = dhcppython.packet.DHCPPacket(op="BOOTREQUEST", htype="ETHERNET", hlen=6, hops=0, xid=random.getrandbits(32), secs=0, flags=0, ciaddr=ipaddress.IPv4Address(0), yiaddr=ipaddress.IPv4Address(0), siaddr=ipaddress.IPv4Address(0), giaddr=ipaddress.IPv4Address(0), chaddr=args.mac_address, sname=b'', file=b'', options=options)
   if dhcp_response:
      # set requested IP Address & ciAddr
      options.remove(options.by_code(50))
      dhcp_release.ciaddr = dhcp_response.yiaddr
   else:
      # set requested IP Address
      dhcp_release.ciaddr = ipaddress.IPv4Address(args.requested_ip_address)

   # send DHCPRELEASE
   logger.trace("Sending DHCPRELEASE: {}".format(dhcp_release))
   logger.info("Sending DHCPRELEASE to {}".format(dhcp_server))
   dhcp_request = send_query(dhcp_socket, dhcp_release, dhcp_server)
   if debug > 1:
      print_dhcp_packet(dhcp_request)


# clean up IP configuration
if tmp_ip:
   delete_ip(args.interface, tmp_ip)

# exit based on warnings/errors
if error_cnt > 0:
   logger.error("DHCP Probe did not complete successfully")
if error_cnt > 1:
   exit(exit_code_error)
if error_cnt > 0:
   exit(exit_code_warning)


