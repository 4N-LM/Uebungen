import os
import sys
def quit():
    clear()
    print("exiting")
    sys.exit()

def clear():
    os.system('cls' if os.name =='nt' else 'clear')

def create_field():
    field = []
    row = [std_empty for i in range(7)]     
    for i in range(0,6):
        field.append(row[:])
    return field


def print_field(field:list):
    for i in range(0,6):
        for j in range(0,7):
            print(field[i][j],end="\t")
        print("\n")


def set_stone(field:list,row:int,player_marc:str="o"):
    if field[5][row] == std_empty:
        field[5][row] = player_marc
        return False
    elif field[0][row] == "O":
        print("Line Full !! \nPlease Enter a new valid Line")
        return True
    else:
        for i in range(0,5):
            if field[i+1][row] != std_empty:
                field[i][row] = "o"
        return False
    
def get_player_input():
    while True:
        try:
            player_input = int(input("Number (1-7) please (0 Terminates Programm): - "))
            player_input -= 1            
            if -1 < player_input < 7:
                return player_input
            if player_input == -1:
                quit()
            print("Number not in defined Area!\t Try again")
        except(TypeError,ValueError):
            print("Not a number!! \t Try again")


def winner_check(field:list):
    for i in range(len(field) - 1):
        for j in range(len(field[i]) - 1):
            if field[i][j] != std_empty:
                try:
                    left_up_check()
                except:
                    print("Error")

std_empty = "x" #standart empty field char
field = create_field()

def left_up_check(posx:int,posy:int,field:list):
    try:
        field[posx][posy] = ""
    except:
        print("Error in left_up_check")




while True:
    clear()
    print_field(field)
    invalid_move = True
    while invalid_move:
        player_input = get_player_input()
        invalid_move = set_stone(field,player_input)
    
