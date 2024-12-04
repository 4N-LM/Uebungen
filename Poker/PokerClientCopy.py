import socket
import tkinter as tk
import time

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

def create_cklicki_bunti():
    root.title("Poker")        
    canvas.create_image(0,0,anchor='nw', image=image,)
    canvas.create_text(500, 360, text='LoremIpsum', tags='table', font=("Arial", 120))
    canvas.pack()
    canvas.create_text(200, 650, text='LoremIpsum', tags='hand', font=("Arial", 120))
    canvas.pack()
    canvas.create_text(900, 100, text='LoremIpsum', tags='pot', font=("Arial", 50))
    canvas.pack()
    button1 = tk.Button(root,text='Hello',command=lambda:send_data('10'),font=('Arial',50))
    button1.place(x=900,y=600)

def send_data(msg:str='Hello there'):    
    data = msg
    client_socket.send(data.encode())

def answer(test:bool=False):
    if not test:
        try:
            while True:
                print('reciving: \n\n')
                data = client_socket.recv(1024)   
                if data.decode() != "":
                    tmp =data.decode().split(':')
                    if len(tmp) != 2:
                        print('Falsche länge: ' + tmp)
                        raise KeyError
                    else:
                        return tmp
        except(KeyboardInterrupt):
            send_data('Exit')
            return False
        except(KeyError):
            print("Übertragungsfehler oder Server Kaput")
            return False
        except:
            print("ein Fehler beim client")
    else:
        time.sleep(3)
        return ['test','test']

def func():
    root.destroy()

def close_connection():
    client_socket.close()

def change_hand(change:str):
    canvas.itemconfig('hand', text=change)
    
def change_table(change:str):
    canvas.itemconfig('table',text=change)
    
def change_pot(change:str):
    canvas.itemconfig('pot',text=change)

init()
global canvas
global root
global image
root = tk.Tk()
canvas = canvas = tk.Canvas(root, width=1080, height=720)
image = tk.PhotoImage(file='Poker2.png')
create_cklicki_bunti()

def update_text():
    x = answer()        # Antwort vom Server als Liste aus 2 Strings
    match x[0]:
        case 'hand':
            change_hand(x[1])
        case 'table':
            change_table(x[1])
        case 'pot':
            change_pot(x[1])
        case 'test':
            print(x[1])
        case 'exit':
            close_connection()
            root.destroy()
            return False
        case _:
            print('Unklare Antwort vom Server')
    root.update_idletasks()    
             
       

root.after(100, update_text)  # Funktion nach 100ms starten
print('Here')
# Tkinter-Hauptschleife
root.mainloop()



close_connection()
