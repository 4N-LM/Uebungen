import socket
import tkinter as tk

root = tk.Tk()
root.title("Poker")
image = tk.PhotoImage(file='Poker2.png')
canvas = tk.Canvas(root, width=540, height=720)
canvas.create_image(0,0,anchor='nw', image=image,)

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

def send_data(msg:str):    
    data = msg
    client_socket.send(data.encode())

def answer():
    try:
        while True:
            data = client_socket.recv(1024)
            if data.decode() != "":
                return data.decode()
            if data.decode().lower() == "exit":
                close_connection()
                return False
    except(KeyboardInterrupt):
        send_data('Exit')
        return False
    except:
        print("ein Fehler beim client")

def close_connection():
    client_socket.close()

init()
canvas.create_text(350, 300, text='LoremIpsum', tags='hand', font=("Arial", 120))
canvas.pack()

def update_text():
    x = answer()  # Antwort vom Server als String
    if x:
        canvas.itemconfig('hand', text=x)
        print(x)
        # Funktion erneut nach 100ms aufrufen
        root.after(100, update_text)
    else:
        print("Ende")
        root.destroy()  # Fenster schließen, wenn keine Antwort mehr kommt

root.after(100, update_text)  # Funktion nach 100ms starten

# Tkinter-Hauptschleife
root.mainloop()



close_connection()
