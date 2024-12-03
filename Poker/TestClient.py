import socket

def init():
    host = input('Server IP:')
    port = int(input('Server Port:'))
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

def send_data(msg:str):    
    data = msg
    client_socket.send(data.encode())

def answer():
    try:
        while True:
            data = client_socket.recv(1024)
            if data.decode() != "":
                return data.decode()
            if data.decode().lower() == "exit":
                close_connection()
    except:
        print("ein Fehler beim client")

def close_connection():
    client_socket.close()

init()
i = 20
while i > 0:
    print(answer())
    i -=1


print('ende')
close_connection()
