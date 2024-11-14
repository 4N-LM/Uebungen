import socket
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('server_ip',type=str,help='Input the Server IP')
parser.add_argument('server_port',type=int,help='Input the Server Port')
parser.add_argument('server_msg',type=str,help='Input the Massage')
args = parser.parse_args()

host = args.server_ip
port = args.server_port

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host, port))

data = args.server_msg
client_socket.send(data.encode())  # Daten senden

client_socket.close()
