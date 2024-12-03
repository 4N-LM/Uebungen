import socket
import Poker

global deck
global clients
clients = []
def selfInit():
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
    print(clients)
    print("Alle Verbindungen hergestellt!")
    deck = Poker.create_deck()

#Karten Verteilen

selfInit()

print(clients)
# Verbindungen verwalten oder schließen

for client_socket, client_address in clients:
    client_socket.send(b"Willkommen auf dem Server!")

print(clients)

while True:
    if not input("Nichts für weiter") == '':
        break


print("Ende")
for client_socket, client_address in clients:
    client_socket.close()
server_socket.close()

