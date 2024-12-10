import socket
import Poker
import random
import time


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
x = ()
def serverConf():
    # Server konfigurieren
    global server_socket
    host = '0.0.0.0'    
    port = 44444

    server_socket.bind((host, port))
    server_socket.listen(1)
    x = (client_socket, client_address) = server_socket.accept()
    print("Alle Verbindungen hergestellt!")
    
    return x


def sendToSingle(msg:str):
    x[0].send(msg.encode()) 
    
def recive_Data():
    try:
        while True:
            sendToSingle('get:get')
            data = x[0].recv(1024)   
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

x = serverConf()
sendToSingle('mony:1000')
time.sleep(5)
while True:
    tmp = recive_Data()[0]
    if tmp == 'Null':
        break
    print(tmp)

sendToSingle('exit:exit')
print("Ende")
x[0].close()
server_socket.close()
print('Alles Beendet')

