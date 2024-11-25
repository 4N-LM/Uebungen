import tkinter as tk
deck = {}
k = 1
for i in range(1, 63):
    if not i in [12,28,44,60]:
        unicode_char = chr(0x1F0A0 + i)
        deck['A' + str(k)] = unicode_char
        k +=1

root = tk.Tk()
root.title("Überschrift")
def print_deck():
    tmp = ''
    num = 0
    for j in range(4):
        for i in range(13):
            num += 1               
            tmp += deck.get('A' + str(num))
        tmp += '\n'
        num += 2
    label = tk.Label(root, text=tmp, font=("Arial", 100))
    label.pack()

print_deck()
#label2 = tk.Label(root, text='Hello World', font=("Arial", 100))
#label2.pack()

root.mainloop()