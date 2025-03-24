import socket
from time import sleep
import random
server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
server_socket.bind(('::1', 12345))
server_socket.listen(5)
while True:
    try:
        client_socket, addr = server_socket.accept()
        print("Connection from: " + str(addr))
        sleep(0.1)
        client_socket.send(b"0")
        while True:
            data = client_socket.recv(1024)
            if data.decode() != "":
                print(data.decode())
                data = str(int(data.decode()) + random.randint(1, 10)).encode()
                client_socket.send(data)
            else:
                break
    except KeyboardInterrupt:
        print("Server beendet.")
        break
server_socket.close()
client_socket.close()

  