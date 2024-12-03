import socket
import tkinter as tk

def init():
    host = input('Server IP:')
    port = int(input('Server Port:'))
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
root = tk.Tk()
root.geometry("1080x720")
bg = tk.PhotoImage(file=r'Poker2.png')

canvas= tk.Canvas( root, width=1080,height=720)
canvas.place(x = 0, y = 0)
canvas.create_image(0,0,image=bg,anchor="nw")
canvas.create_text(500,350,
                   text='1,2,3,4,5',
                   fill='black',
                   font=('Arial',48,'bold'),
                   tags='table'
                   )
canvas.create_text(50,650,
                   text='1,2',
                   fill='black',
                   font=('Arial',48,'bold'),
                   tags='hand'
                   )
def changeText(tag:str,text:str):
    canvas.itemconfig(tag,text=text)
root.mainloop()




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
    except:
        print("ein Fehler beim client")

def close_connection():
    client_socket.close()