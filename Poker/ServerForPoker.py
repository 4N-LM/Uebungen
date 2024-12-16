import socket
import Poker
import random
import time

class Player:
    def __init__(self,socket:socket,address,num:int):
        self.address = address
        self.name = 'John' + str(num)
        self.socket = socket
        self.hand = ''
        self.money = 0
        self.bet = 0
        self.activePlayer = False
        self.score = 0
        
    def __eq__(self, other):
        return self.name == other.name
    
    def __str__(self):
        tmp = 'Name: ' + self.name + ', Money: ' + str(self.money) + ', Active: ' + str(self.activePlayer)
        return tmp
    
    def __hash__(self):
        return hash((self.name,self.socket,self.hand,self.money,self.bet,self.activePlayer))

    def send(self,msg:str):
        self.socket.send(msg.encode())
        time.sleep(0.1)

global deck
global clients
global pot
global Test
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
def serverConf():
    # Server konfigurieren
    global server_socket
    host = '0.0.0.0'
    Test = False
    # Port abfragen, Standard ist 44844
    port = input("Please enter a port (if empty, it's <44844>): ")
    if port == "":
        port = 44844
    else:
        port = int(port)
    if port == 44444:
        Test = True        
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
        x:Player = Player(client_socket,client_address,i)
        clients.append(x)
    print("Alle Verbindungen hergestellt!")
    return (clients,Test)

def sendToAll(msg:str):
    print(f'sending to all: {msg}') 
    for i in range(len(clients)):
        clients[i].send(msg)
    time.sleep(0.4)

def sendToSingle(msg:str,player:Player):
    print(f'sending: {msg} to {player.name}')
    player.send(msg)
    time.sleep(0.4)

def createCardSupset(lengh:int = 2):
    tmp = []
    for i in range(lengh):
        while True:
            x = str(random.randint(1,52))
            if not deck.get(x).active:
                tmp.append(deck.get(str(x)))
                deck.get(x).active = True
                break
    return tmp

def send_hand(cards:str):
    return 'hand:' + cards

def send_table(cards:str):
    return 'table:' + cards

def send_pot(money:int):
    return 'pot:' + str(money)

def send_bet(money:int):
    return 'bet:' + str(money)

def recive_Data(player:Player):
    x = player.socket
    sendToSingle('get:get',player)
    try:
        while True:
            data = x.recv(1024)   
            if data.decode() != "":
                tmp:list =data.decode().split(':')
                print(f'\t\t\t From {player.name} resived: {tmp[0]}')
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

def gettingSingleBet(bet:int,player:Player):
    sendToAll('turn:' + player.name)
    sendToAll(send_bet(bet))
    data = recive_Data(player)[0]
    if data != 'fold':
        return int(data)
    else:
        return -99999

def gettingClientsInOrder():
    tmp = []
    for j in range(2):
        for i in range(len(active_player)):
                if active_player[i].activePlayer and active_player[i] not in tmp:
                    tmp.append(active_player[i])
                    active_player[i].activePlayer = False
                    if active_player[i] == active_player[-1]:
                        active_player[0].activePlayer = True
                    else:
                        active_player[i + 1].activePlayer = True
    return tmp

def checkAllSameBets(allPlayer:list):
    tmp = False
    for i in range(len(allPlayer)):
        if allPlayer[0].bet == allPlayer[i].bet:
            tmp = True
        else:
            tmp = False
            break
    return tmp

def gettingAllBets(pot:int):
    bet = 0
    if pot == 0:
        bet = 10
    clientsInOrder =  []  
    sendToAll(send_pot(pot))
    if len(active_player) < 2:
        if Test:
            bet = gettingSingleBet(bet,active_player[0])
            clients[0].money -= bet
            sendToSingle('mony:' + str(active_player[0].money),active_player[0])
            pot += bet
            return pot
        else:
            return pot
        
    clientsInOrder = gettingClientsInOrder()    
    allBetsUnequal = True
    while allBetsUnequal:
        for i in range(len(clientsInOrder)):
            if len(clientsInOrder) == 1:
                bet = clientsInOrder[0].bet
                break
            
            bet = gettingSingleBet(bet,clientsInOrder[i])
            
                
            if bet == -1:
                print('Fold')
                active_player.remove(clientsInOrder[i])
                clientsInOrder.pop(i)
                bet = clientsInOrder[i].bet
                break
            clientsInOrder[i].bet = bet        
                
        if len(active_player) > 1:
            allBetsUnequal = not checkAllSameBets(active_player)
        else:
            break
            
    for i in active_player:
        print('Player: ' + i.name + '\nBet: ' + str(i.bet) + '\nPot: ' + str(pot))
        pot += i.bet
        i.money -= i.bet
        i.send('mony:' + str(i.money))
    print('Pot Bevore Return: ' + str(pot))
    return pot

def stringToList(string:str):
    tmp = []
    for i in string:
        tmp.append(i)
    return tmp

def cardlistToString(listee:list):
    tmp = ''
    for i in listee:
        tmp += i.symbol
    return tmp

def evalHelper(winners:list,depth:int):
    highest = [winners[0]]
    for i in winners:
        if i == highest[0]:
            continue
        else:
            if i.score[depth] > highest[0].score[depth]:
                highest.clear
                highest[0] = i
            if i.score == highest[0].score:
                highest.append(i)
    return highest

def finalEvaluation(players:list):
    for i in players:
        i.score = Poker.highestCheck(i.hand,table)
    
    x = evalHelper(players,0)
    if len(x) > 1:
        x = evalHelper(x,1)
        if len(x) >1:
            x = evalHelper(x,2)
            if len(x) >1:
                y = ''
                for i in x:
                    y += i
                return tuple(y)
            else:
                return (x[0],)
        else:
            return (x[0],)
    else:
        return (x[0],)

Test = False
conf = serverConf()
clients = conf[0]
Test = conf[1]
if Test:
    print('''
        ___________     _________       ________        ___________
             |          |               |                    |
             |          |               |                    |
             |          |_____          |_______             |
             |          |                       |            |
             |          |                       |            |
             |          |________       ________|            |
              
              ''')
sendToAll('mony:2000')
for i in clients:
    i.send('name:name')
    i.name = recive_Data(i)[0]   
    i.money=2000

while True:
    sendToAll(send_table(''))
    sendToAll('info: ')
    active_player = clients[:]
    deck = Poker.create_deck()
    table = createCardSupset(3)

    for i in active_player:
        i.hand = createCardSupset(2)
        i.send(send_hand(cardlistToString(i.hand)))
        i.bet = 0                            
    
    clients[0].activePlayer = True

    pot = 0
    pot = gettingAllBets(pot)  #runde eins

    sendToAll(send_table(cardlistToString(table)))
    table += createCardSupset(1)

    pot = gettingAllBets(pot)  #runde zwei
    sendToAll(send_table(cardlistToString(table)))
    table += createCardSupset(1)

    pot = gettingAllBets(pot)  #runde drei
    sendToAll(send_table(cardlistToString(table)))

    pot = gettingAllBets(pot)  #runde vier

    #auswertung und Geldverteilen
    if len(active_player) == 1:
        active_player[0].money += pot
        sendToSingle('mony:' + str(active_player[0].money),active_player[0])
        sendToAll('info:Winner is ' + active_player[0].name)
    else:
        winner = finalEvaluation(active_player)
        if len(winner) > 1:
            moneten = pot // len(winner)
            tmp:str = ""
            for i in winner:
                i.money += moneten
                sendToSingle('mony:' + str(i.money),i)
                tmp += i.name + ' '
            sendToAll('info:Winner is ' + tmp)
        else:
            winner[0].money += pot
            print('Winner: ' + winner[0].name)
            sendToSingle('mony:' + str(winner[0].money),winner[0])
            sendToAll('info:Winner is ' + winner[0].name + ' with ' + str(winner[0].score[0]))
        
    if input("Again? : - ").lower() not in ['yes','y','j','ja','yo']:
        break

sendToAll('exit:exit')
print("Ende")
for i in range(len(clients)):
    clients[i].socket.close()
server_socket.close()
print('Alles Beendet')

