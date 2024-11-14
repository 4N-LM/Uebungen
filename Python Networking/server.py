import socket

host = '0.0.0.0'
port = 44844

server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(1)
active = True
while active:   
    print("Waiting for Connection")
    client_socket, client_address = server_socket.accept()
    print(f"Connection to {client_address} established")
    data = client_socket.recv(1024)
    print("data: ", data.decode())
    active = bool(input("0 for Quit, 1 for again: "))

client_socket.close()
server_socket.close()