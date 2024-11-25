import tkinter as tk
import random

window = tk.Tk()

            
def create_dice_deck():
    loool = []
    for i in range(6):
        unicode_char = chr(0x2681 + i)
        loool += unicode_char
    return loool

def window_init():
    global window
    window.title('Ein Lustiges Vidget')
    icon =  tk.PhotoImage(file=r'C:\Users\LauridsMäntz\Documents\GitHub\Uebungen\Testing\logo.png') 
    window.iconphoto(True,icon)
    window.config(background='black')

window_init()
dice_deck = create_dice_deck()[:]



def click():
    dice_str = ''
    for i in range(5):
        dice_str += dice_deck[random.randint(0, 5)]
    label.config(text=dice_str)

button = tk.Button(window,text='Random Kniffel!')
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

