import socket
import Poker
import random
import time

global deck
global clients
def serverConf():
    # Server konfigurieren
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '0.0.0.0'

    # Port abfragen, Standard ist 44844
    port = input("Please enter a port (if empty, it's <44844>): ")
    if port == "":
        port = 44844
    else:
        port = int(port)

    # Anzahl der Spieler festlegen
    number_of_players = int(input("Enter the number of players: "))
    server_socket.bind((host, port))
    server_socket.listen(number_of_players)
    print(f"Server gestartet und wartet auf {number_of_players} Verbindungen...")

    # Verbindungen annehmen
    clients=[]
    for i in range(number_of_players):
        client_socket, client_address = server_socket.accept()
        print(f"Verbindung {i + 1} zu {client_address} hergestellt")

        clients.append((client_socket, client_address))
    print("Alle Verbindungen hergestellt!")
    return clients

def sendToAll(msg:str):
    for i in range(len(clients)):
        clients[i][0].send(msg.encode())

def sendToSingle(msg:str,num:int):
    clients[num][0].send(msg.encode())

def createCardSupset(lengh:int = 2):
    tmp = ''
    for i in range(lengh):
        while True:
            x = str(random.randint(1,52))
            if not deck.get(x).active:
                tmp += deck.get(str(x)).symbol
                deck.get(x).active = True
                break
    return tmp


clients = serverConf()
deck = Poker.create_deck()
#Karten Verteilen
for i in clients:
    i[0].send(createCardSupset(2).encode())

time.sleep(1)
sendToAll('All')
time.sleep(1)
for i in range(len(clients) - 1):
    sendToSingle(str(i),i)
# Verbindungen verwalten oder schließen

for client_socket, client_address in clients:
    client_socket.send(b"Willkommen auf dem Server!")



print("Ende")
for client_socket, client_address in clients:
    client_socket.close()
#server_socket.close()

