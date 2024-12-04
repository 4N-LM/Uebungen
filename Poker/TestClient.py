import socket

def init():
    host = input('Server IP:')
    if host == '':
        host = '127.0.0.1'

    port = input('Server Port:')
    if port == '':
        port = '44844'
    port = int(port)

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
                return False
    except(KeyboardInterrupt):
        send_data('Exit')
        return False
    except:
        print("ein Fehler beim client")

def close_connection():
    client_socket.close()

init()
while True:
    x = answer()
    if not x:
        break
    print(x)


print('ende')
close_connection()
