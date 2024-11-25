import tkinter as tk
deck = {}
for i in range(1, 15):
    unicode_char = chr(0x1F0D0 + i)
    deck['A' + str(i)] = unicode_char

root = tk.Tk()
root.title("Überschrift")
tmp = ''
num = 0
lol = deck.get('A11') + deck.get('A12') + deck.get('A13') 
print(ord(deck.get('A11')))
print(ord(deck.get('A12')))
print(ord(deck.get('A13')))
for j in range(1):
    for i in range(14):
        num += 1
        print(i , j , num)
        tmp += deck.get('A' + str(num))
        
    tmp += '\n'
    num += 2
label = tk.Label(root, text=lol, font=("Arial", 300))
label.pack()
root.mainloop()