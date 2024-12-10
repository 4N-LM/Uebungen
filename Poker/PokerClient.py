import socket
import tkinter as tk
import threading
from time import sleep as wait

def init():
    host = get_input(15,'Server IP Bitte: - ',str,7)
    if host == '':
        host = '127.0.0.1'

    port = get_input(5,'Server Port Bitte: - ',str,4)
    if port == '':
        port = '44844'
    port = int(port)
    
    name = get_input(15,'Deinen Namen Bitte(2-15 Buchstaben): - ',str,2)

    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    return name

def get_input(max:int,text:str,datatype:type,min:int=1):
    while True:
        tmp = input(text)
        if (min < len(tmp) <= max or len(tmp) == 0) and type(tmp) == datatype:
            break
        else:
            print('Flascher input: Try again\n')
    return tmp

# Funktion zum Empfangen von Daten aus dem Server
def receive_data():
    while True:
        try:
            data = client_socket.recv(1024)   
            if data.decode() != "":
                tmp = data.decode().split(':')
                if len(tmp) == 2:
                    # Daten an die Haupt-GUI weitergeben
                    root.after(0, process_server_data, tmp)
                else:
                    print('Falsche Länge der Antwort vom Server:', tmp)
        except (KeyboardInterrupt, ConnectionResetError):
            print("Verbindung zum Server wurde getrennt.")
            break
        except Exception as e:
            print(f"Fehler beim Empfangen von Daten: {e}")
            break

def process_server_data(data):
    # Diese Funktion wird im Hauptthread aufgerufen und ändert die GUI
    global darfSenden  # Zugriff auf die globale Variable
    
    if data[0] in ['hand','table','pot','turn','mony','bet','info']:
        change_text(data[0],data[1])
        return
    match data[0]:
        case 'get':
            darfSenden = True  # Erlaube das Senden von Daten
        case 'test':
            print(data[1])
        case 'exit':
            close_connection()
            root.destroy()
        case 'name':
            darfSenden = True
            send_data(name)
        case _:
            print('Unklare Antwort vom Server')

def create_cklicki_bunti():
    root.title("Poker")         
    canvas.create_image(0, 0, anchor='nw', image=image)
    canvas.create_text(500, 360, text='', tags='table', font=("Arial", 120))
    canvas.pack()
    canvas.create_text(200, 650, text='', tags='hand', font=("Arial", 120))
    canvas.pack()
    canvas.create_text(900, 100, text='pot', tags='pot', font=("Arial", 50))
    canvas.pack()
    canvas.create_text(700, 100, text='bet', tags='bet', font=("Arial", 50))
    canvas.pack()
    canvas.create_text(350, 100, text='', tags='turn', font=("Arial", 35))
    canvas.pack()    
    canvas.create_text(900, 450, text='mn', tags='mony', font=("Arial", 50))
    canvas.pack()
    canvas.create_text(780, 550, text='10', tags='selfbet', font=("Arial", 50))
    canvas.pack()
    canvas.create_text(450, 250, text='', tags='info', font=("Arial", 35))
    canvas.pack()
    button1 = tk.Button(root, text='Rise', command=lambda: send_data(canvas.itemcget('selfbet','text') if canvas.itemcget('selfbet','text') >= canvas.itemcget('bet','text') else canvas.itemcget('bet','text')), font=('Arial', 50))
    button1.place(x=700, y=600)
    button2 = tk.Button(root, text='Fold', command=lambda: send_data('0'), font=('Arial', 50))
    button2.place(x=900, y=600)
    button3 = tk.Button(root, text='+', command=lambda: change_text('selfbet',str(int(canvas.itemcget('selfbet','text')) + 10) if int(canvas.itemcget('selfbet','text')) + 10 <= int(canvas.itemcget('mony','text')) else int(canvas.itemcget('mony','text'))), font=('Arial', 50))
    button3.place(x=630, y=500)
    button4 = tk.Button(root, text='-', command=lambda: change_text('selfbet',str(int(canvas.itemcget('selfbet','text')) - 10)) if int(canvas.itemcget('selfbet','text')) > 10 else 10 , font=('Arial', 50))
    button4.place(x=870, y=500)
    button1 = tk.Button(root, text='Call', command=lambda: send_data(canvas.itemcget('bet','text')), font=('Arial', 50))
    button1.place(x=600, y=600)
    
def send_data(msg: str):
    global darfSenden  # Zugriff auf die globale Variable
    if darfSenden:
        data = msg
        client_socket.send(data.encode())
        darfSenden = False      # Senden wieder deaktivieren
        wait(0.4)

def change_text(tag: str, change: str):
    canvas.itemconfig(tag, text=change)
    
def close_connection():
    client_socket.close()

# Hauptteil des Programms
global darfSenden
darfSenden = False  # Initialwert

name = init()

global canvas
global root
global image

root = tk.Tk()
canvas = tk.Canvas(root, width=1080, height=720)
image = tk.PhotoImage(file='Poker2.png')
create_cklicki_bunti()

# Starte den Empfang von Daten im separaten Thread
receive_thread = threading.Thread(target=receive_data, daemon=True)
receive_thread.start()

root.mainloop()
