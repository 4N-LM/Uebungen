from PIL import Image, ImageTk  # Pillow für Bildskalierung ###
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
    global darfSenden  # Zugriff auf die globale Variable
    
    if data[0] in ['hand','table','pot','turn','mony','bet','info']:
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
        case 'name':
            darfSenden = True
            send_data(name)
        case _:
            print('Unklare Antwort vom Server')

def create_clickable_gui():  ### (Funktion umbenannt und angepasst)
    root.title("Poker")
    canvas.pack(fill=tk.BOTH, expand=True)  ###

    # Hintergrundbild laden
    global bg_image, bg_photo ### (Globale Variablen für das Hintergrundbild hinzugefügt)
    bg_image = Image.open("Poker2.png")  ### (Bild mit Pillow geöffnet)
    bg_photo = ImageTk.PhotoImage(bg_image)  ###
    canvas.create_image(0, 0, anchor='nw', image=bg_photo, tags='background') ### (Hintergrundbild mit Tag erstellt)

    # Dynamisches Anpassen des Hintergrundbilds
    root.bind("<Configure>", resize_background)  ### (Event-Bindung hinzugefügt)

    # Platzieren der Texte und Buttons
    canvas.create_text(500, 360, text='', tags='table', font=("Arial", 120))
    canvas.create_text(200, 650, text='', tags='hand', font=("Arial", 120))
    canvas.create_text(900, 100, text='pot', tags='pot', font=("Arial", 50))
    canvas.create_text(700, 100, text='bet', tags='bet', font=("Arial", 50))
    canvas.create_text(350, 100, text='', tags='turn', font=("Arial", 35))   
    canvas.create_text(900, 450, text='mn', tags='mony', font=("Arial", 50))
    canvas.create_text(780, 550, text='10', tags='selfbet', font=("Arial", 50))
    canvas.create_text(450, 250, text='', tags='info', font=("Arial", 35))

    # Buttons relativ positionieren
    create_button('Rise', lambda: send_data(canvas.itemcget('selfbet', 'text') if canvas.itemcget('selfbet', 'text') >= canvas.itemcget('bet', 'text') else canvas.itemcget('bet', 'text')), 0.65, 0.8) ###
    create_button('Fold', lambda: send_data('-1'), 0.85, 0.8) ###
    create_button('+', lambda: change_text('selfbet', str(int(canvas.itemcget('selfbet', 'text')) + 10) if int(canvas.itemcget('selfbet', 'text')) + 10 <= int(canvas.itemcget('mony', 'text')) else int(canvas.itemcget('mony', 'text')), ), 0.6, 0.7) ###
    create_button('-', lambda: change_text('selfbet', str(int(canvas.itemcget('selfbet', 'text')) - 10) if int(canvas.itemcget('selfbet', 'text')) > 10 else 10), 0.85, 0.7) ###
    create_button('Call', lambda: send_data(canvas.itemcget('bet', 'text')), 0.4, 0.8) ###

def resize_background(event):  ### (Funktion hinzugefügt)
    global bg_image, bg_photo  ###
    # Hintergrundbild anpassen
    new_width = event.width  ###
    new_height = event.height  ###
    resized_image = bg_image.resize((new_width, new_height), Image.Resampling.LANCZOS)  ### (Bildgröße anpassen)
    bg_photo = ImageTk.PhotoImage(resized_image)  ###
    canvas.itemconfig('background', image=bg_photo)  ### (Canvas-Bild aktualisieren)

def create_button(text, command, relx, rely):  ### (Hilfsfunktion für Buttons hinzugefügt)
    button = tk.Button(root, text=text, command=command, font=('Arial', 20))  ###
    button.place(relx=relx, rely=rely, anchor='center')  ### (Button relativ positionieren)

def send_data(msg: str):
    global darfSenden  # Zugriff auf die globale Variable
    if darfSenden:
        data = msg
        client_socket.send(data.encode())
        darfSenden = False      # Senden wieder deaktivieren
        change_text('selfbet', '30')
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
root = tk.Tk()
canvas = tk.Canvas(root, width=1080, height=720)

create_clickable_gui() ###

# Starte den Empfang von Daten im separaten Thread
receive_thread = threading.Thread(target=receive_data, daemon=True)
receive_thread.start()

root.mainloop()
