import socket
import time

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '0.0.0.0'
port = input("Please Enter a port(if empty its <44844>)")       
if port == "":
    port = 44844
else:
     port = int(port)

server_socket.bind((host, port))
server_socket.listen(1)

print("Waiting")
client_socket1, client_address1 = server_socket.accept()
#client_socket2, client_address2 = server_socket.accept()

print(f"Connection 1 to {client_address1} established")
#print(f"Connection 2 to {client_address2} established")

game = True

while game:
    print("Player ONE's Turn")
    try:
        data = client_socket1.recv(1024)         
        if not data:
            print("Connection closed by Client 1.")
            game=False
            break

        print(f"Data:\n {data.decode()}")
        time.sleep(3)
        client_socket1.send(data)
        print("Data sent to Client")
    except Exception as e:
        print(e)
        break
    
    
client_socket1.close()
server_socket.close()
