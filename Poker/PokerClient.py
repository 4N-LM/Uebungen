import socket
import tkinter as tk
import threading

def init():
    host = input('Server IP:')
    if host == '':
        host = '127.0.0.1'

    port = input('Server Port:')
    if port == '':
        port = '44844'
    port = int(port)

    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

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
    
    global darfSenden
    
    if data[0] in ['hand','table','pot','turn',]:
        change_text(data[0],data[1])
        return
    match data[0]:
        case 'get':
            darfSenden = True
        case 'test':
            print(data[1])
        case 'exit':
            close_connection()
            root.destroy()
        case _:
            print('Unklare Antwort vom Server')

def create_cklicki_bunti():
    root.title("Poker")        
    canvas.create_image(0, 0, anchor='nw', image=image)
    canvas.create_text(500, 360, text='LoremIpsum', tags='table', font=("Arial", 120))
    canvas.pack()
    canvas.create_text(200, 650, text='LoremIpsum', tags='hand', font=("Arial", 120))
    canvas.pack()
    canvas.create_text(900, 100, text='LoremIpsum', tags='pot', font=("Arial", 50))
    canvas.pack()
    canvas.create_text(350, 100, text='LoremIpsum', tags='turn', font=("Arial", 50))
    canvas.pack()    
    canvas.create_text(900, 450, text=str(0), tags='money', font=("Arial", 50))
    canvas.pack()
    button1 = tk.Button(root, text='Hello', command=lambda: send_data('10',darfSenden), font=('Arial', 50))
    button1.place(x=900, y=600)

def send_data(msg:str,darf:bool=False):
    if darf:
        data = msg
        client_socket.send(data.encode())
        darfSenden = False

def change_text(tag:str,change: str):
    canvas.itemconfig(tag, text=change)
    
def close_connection():
    client_socket.close()

# Hauptteil des Programms
global darfSenden; darfSenden = False
init()

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

