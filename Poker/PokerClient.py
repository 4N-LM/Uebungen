import socket
import tkinter as tk

root = tk.Tk()
root.title("Poker")
image = tk.PhotoImage(file='Poker2.png')
canvas = tk.Canvas(root, width=1080, height=720)
canvas.create_image(0,0,anchor='nw', image=image,)

def init():
    host = 0#input('Server IP:')
    if host == '':
        host = '127.0.0.1'

    port = 0#input('Server Port:')
    if port == '':
        port = '44844'
    port = int(port)

    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 44844))

def send_data(msg:str):    
    data = msg
    client_socket.send(data.encode())

def answer():
    try:
        while True:
            data = client_socket.recv(1024)            
            if data.decode() != "":
                tmp =data.decode().split(':')
                if len(tmp) > 2 or len(tmp) < 2:
                    raise KeyError
                else:
                    return tmp
    except(KeyboardInterrupt):
        send_data('Exit')
        return False
    except(KeyError):
        print("Übertragungsfehler oder Server Kaput")
    except:
        print("ein Fehler beim client")

def close_connection():
    client_socket.close()

def change_hand(change:str):
    canvas.itemconfig('hand', text=change)
    
def change_table(change:str):
    canvas.itemconfig('table',text=change)
    
def change_pot(change:str):
    canvas.itemconfig('pot',text=change)


init()
canvas.create_text(500, 360, text='LoremIpsum', tags='table', font=("Arial", 120))
canvas.pack()
canvas.create_text(200, 650, text='LoremIpsum', tags='hand', font=("Arial", 120))
canvas.pack()
canvas.create_text(900, 100, text='LoremIpsum', tags='pot', font=("Arial", 50))
canvas.pack()


def update_text():
    x = answer()  # Antwort vom Server als Liste aus 2 Strings
    match x[0]:
        case 'hand':
            change_hand(x[1])
        case 'table':
            change_table(x[1])
        case 'pot':
            change_pot(x[1])
        case 'exit':
            close_connection()
            root.destroy()
            return False
        case _:
            print('Unklare Antwort vom Server')      
             
    root.after(100, update_text)   

root.after(100, update_text)  # Funktion nach 100ms starten

# Tkinter-Hauptschleife
root.mainloop()



close_connection()
