import socket
import Poker
import random
import time

global deck
global clients
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
def serverConf():
    # Server konfigurieren
    global server_socket
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

def send_hand(cards:str):
    return 'hand:' + cards

def send_table(cards:str):
    return 'table:' + cards

def send_pot(money:int):
    return 'pot:' + str(money)

clients = serverConf()
deck = Poker.create_deck()
#Karten Verteilen
for i in range(len(clients)):
    sendToSingle(send_hand(createCardSupset(2)),i)
    time.sleep(0.1)
sendToAll(send_table(createCardSupset(5)))

time.sleep(3)

#for client_socket, client_address in clients:
 #   client_socket.send(b"Willkommen auf dem Server!")


sendToAll('exit:exit')
print("Ende")
for client_socket, client_address in clients:
    client_socket.close()
server_socket.close()
print('Alles Beendet')

