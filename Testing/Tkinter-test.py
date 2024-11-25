import tkinter as tk
from tkinter.simpledialog import askstring

deck = {}
window = tk.Tk()
count = 0
def click():
    global count
    count +=1
    label.config(text=deck.get('A' + str(count)))

def create_deck():
    global deck
    k = 1
    for i in range(1, 63):
        if not i in [12,15,16,28,31,32,44,47,48,60]:
            unicode_char = chr(0x1F0A0 + i)
            deck['A' + str(k)] = unicode_char
            k +=1



def window_init():
    global window
    window.title('Ein Lustiges Vidget')
    icon =  tk.PhotoImage(file=r'C:\Users\LauridsMäntz\Documents\GitHub\Uebungen\Testing\logo.png') 
    window.iconphoto(True,icon)
    window.config(background='black')

window_init()
create_deck()

button = tk.Button(window,text='Ich bin ein Knopf!')
button.config(command=click,
              font=('Ink Free',50,'bold'),
              bg='#ff6200',
              fg='#fffb1f',
              activebackground='#ff1500',
              activeforeground='#fffb1f')

label = tk.Label(window,
                 text='Ein Text!',
                 font=('Arial',200),
                 cursor='heart',
                 takefocus=True,
                 bg='black',
                 fg='#00FF00')
#label.place(x=100,y=0)

label.pack()
button.pack()
window.mainloop() #place window on screen + eventlistener

