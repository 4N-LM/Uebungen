import socket
import random

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '0.0.0.0'
port = 44844       
server_socket.bind((host, port))
server_socket.listen(2)

print("Waiting")
client_socket1, client_address1 = server_socket.accept()
client_socket2, client_address2 = server_socket.accept()

print(f"Connection 1 to {client_address1} established")
print(f"Connection 2 to {client_address2} established")

game = True
player_one_active = True

if bool(random.randint(0,1)):
    player_one_active = True
    client_socket1.send(b"True")
    client_socket2.send(b"False")
    print("Player ONE starts")
else:
    player_one_active = False
    client_socket1.send(b"False")
    client_socket2.send(b"True")
    print("Player TWO starts")

while game:
    if player_one_active:
        print("Player ONE's Turn")
        player_one_active = False
        try:
            data = client_socket1.recv(1024)         
            if not data:
                print("Connection closed by Client 1.")
                game=False
                break
            if "True" in data.decode():
                client_socket2.send(b"lost")
                game = False
                break

            print(f"Data:\n {data.decode()}")
            client_socket2.send(data)
            print("Data sent to Client 2")
            print("1")
        except Exception as e:
            print(e)
        print("2")
    else:
        print("Player TWO's Turn")
        player_one_active = True
        try:
            data = client_socket2.recv(1024)         
            if not data:
                print("Connection closed by Client 2.")
                game=False
                break
            if "True" in data.decode():
                client_socket1.send(b"lost")
                game = False
                break
            print(f"Data:\n {data.decode()}")
            client_socket1.send(data)
            print("Data sent to Client 1")
        except Exception as e:
            print(e)








    
client_socket1.close()
client_socket2.close()
server_socket.close()
