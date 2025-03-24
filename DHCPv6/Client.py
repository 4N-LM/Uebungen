import socket
import time
import random
client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
client_socket.connect(('::1', 12345))

while True:
    data = client_socket.recv(1024)
    if data.decode() != "":
        print(data.decode())
        data = str(int(data.decode()) - random.randint(1, 10)).encode()
        client_socket.send(data)
        
client_socket.close()