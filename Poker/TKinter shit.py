import tkinter as tk

def update_text():
    canvas.itemconfig("text_tag", text="Automatisch geändert!")
    root.after(2000, reset_text)  # Nach 2 Sekunden zurücksetzen

def reset_text():
    canvas.itemconfig("text_tag", text="Warten...")

root = tk.Tk()
root.title("Zeitgesteuerte Ereignisse")

canvas = tk.Canvas(root, width=400, height=200, bg="lightblue")
canvas.pack()

canvas.create_text(200, 100, text="Warten...", font=("Arial", 24), tags="text_tag")

# Timer starten
root.after(3000, update_text)  # Nach 3 Sekunden ändern

root.mainloop()