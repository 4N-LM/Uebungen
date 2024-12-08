import socket
import threading

def init():
    host = input('Server IP:')
    if host == '':
        host = '127.0.0.1'

    port = input('Server Port:')
    if port == '':
        port = '44844'
    port = int(port)

     
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    return client_socket

def send_data():
    while True: 
        data = input("Input data to send: \n")
        client.send(data.encode())

def answer():
    try:
        while True:
            data = client.recv(1024)
            if data.decode() != "":
                print(data)
            if data.decode().lower() == "exit":
                close_connection()
                
    except(KeyboardInterrupt):
        send_data('Exit')
        return False
    except:
        print("ein Fehler beim client")

def close_connection():
    client.close()

client = init()

receive_thread = threading.Thread(target=answer, daemon=True)
receive_thread.start()
send_data()

print('ende')
close_connection()
