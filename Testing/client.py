import socket

def init(IP:str,port_nr:int):
    host = IP
    port = port_nr
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

if __name__ == '__main__':
    init('127.0.0.1',44844)


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