import socket
import Poker
import random
import time

global deck
global clients
global pot
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
    activePlayer = False
    name = 'John'
    for i in range(number_of_players):
        client_socket, client_address = server_socket.accept()
        print(f"Verbindung {i + 1} zu {client_address} hergestellt")

        clients.append(list((client_socket, client_address, activePlayer, name)))
    print("Alle Verbindungen hergestellt!")
    return clients

def sendToAll(msg:str):
    print(f'sending to all: {msg}') 
    for i in range(len(clients)):
        clients[i][int(0)].send(msg.encode())
    time.sleep(0.4)

def sendToSingle(msg:str,num:int):
    print(f'sending to {num}: {msg}')
    clients[num][0].send(msg.encode())
    time.sleep(0.4)

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

def recive_Data(x:socket):
    x.send('get:get'.encode())
    try:
        while True:
            data = x.recv(1024)   
            if data.decode() != "":
                tmp:list =data.decode().split(':')
                print(tmp)
                return tmp
    except(KeyboardInterrupt):
        print('Why?')
        return ['Null']
    except(KeyError):
        print("Übertragungsfehler oder Server Kaput")
        return ['Null']
    except Exception as e:
        print(e)
        print("ein Fehler beim client")
        return ['Null']
  
def getting_all_bets():
    bet = 10
    clientsInOrder =  []  
    if len(clients) < 2:
        sendToSingle('turn:' + clients[0][3],0)
        sendToAll(send_pot(bet))
        return int(recive_Data(clients[0][0])[0])
      
    for j in range(2):
        for i in range(len(clients)):
                if clients[i][2] and clients[i] not in clientsInOrder:
                    clientsInOrder.append(clients[i])
                    clients[i][2] = False
                    if clients[i] == clients[-1]:
                        clients[0][2] = True
                    else:
                        clients[i + 1][2] = True
                    
    for i in range(len(clientsInOrder) - 1):
        sendToAll('turn:' + clients[i][3])
        sendToAll(send_pot(bet))
        sendToSingle('get:bet',i)
        data = recive_Data(clientsInOrder[i][0])
        print(data[0])
        bet = int(data[0])
        pot += (int(data[0]))
        clients[i][2] = False
        print(f'I: {i}')
    return pot   


clients = serverConf()
active_player = clients[:]
deck = Poker.create_deck()
table = createCardSupset(3)
#Karten Verteilen
for i in range(len(clients)):
    sendToSingle(send_hand(createCardSupset(2)),i)
    sendToSingle('name:name',i)
    clients[i][3] = recive_Data(clients[i][0])[0]
    print(clients[i][3])

clients[0][2] = True
#erste runde einsätze

pot = 0
pot += getting_all_bets()

#ersten 3 Table Karten
sendToAll(send_table(table))
table += createCardSupset(1)
#zweite runde setzten

pot += getting_all_bets()

sendToAll(send_table(table))
table += createCardSupset(1)

pot += getting_all_bets()

sendToAll(send_table(table))

pot += getting_all_bets()

#auswertung und Geldverteilen

#sendToAll(send_table(createCardSupset(5)))

#time.sleep(3)

#for client_socket, client_address in clients:
 #   client_socket.send(b"Willkommen auf dem Server!")


sendToAll('exit:exit')
print("Ende")
for i in range(len(clients)):
    clients[i][0].close()
server_socket.close()
print('Alles Beendet')

