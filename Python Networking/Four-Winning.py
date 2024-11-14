import os
import sys
from subprocess import run 

def quit():
    clear()
    print("exiting")
    sys.exit()

def clear():
    os.system('cls' if os.name =='nt' else 'clear')

def create_field():
    field = []
    row = [std_empty for i in range(7)]
    #row = [i for i in range(7)]                     #Field only for Tests 
    for i in range(0,6):
        field.append(row[:])
    return field

def print_field(field:list):
    for i in range(0,6):
        for j in range(0,7):
            print(field[i][j],end="\t")
        print("\n")

def set_stone(field:list,row:int,player_marc:str):
    if field[5][row] == std_empty:
        field[5][row] = player_marc
        return False
    elif field[0][row] != std_empty:
        print("Line Full !! \nPlease Enter a new valid Line")
        return True
    else:
        for i in range(0,5):
            if field[i+1][row] != std_empty:
                field[i][row] = player_marc
                break
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
    row_count_left = [0]
    row_count_right = [0]
    row_count_up = [0]
    row_count_side = [0]
    for i in range(len(field)):
        for j in range(len(field[i])):
            if field[i][j] != std_empty:
                if  i > 2 and j > 2:
                    row_count_left.append(left_up_check(i,j,field))
                if  i > 2:
                    row_count_up.append(upwards_check(i,j,field))
                if  j < 4:
                    row_count_side.append(sideways_check(i,j,field))
                if  i > 2 and j < 4:
                    row_count_right.append(right_up_check(i,j,field))
            if 4 in row_count_side or 4 in row_count_left or 4 in row_count_right or 4 in row_count_up:
                break
    row_count_left.sort();row_count_right.sort();row_count_side.sort();row_count_up.sort()
    #return "left: " + str(row_count_left[-1]) + "\nright: " + str(row_count_right[-1]) + "\nup: " + str(row_count_up[-1]) + "\nsideways: " + str(row_count_side[-1])
    return str(row_count_left[-1]) + str(row_count_right[-1]) + str(row_count_up[-1]) + str(row_count_side[-1])

def left_up_check(posx:int,posy:int,field:list,counter:int=1):
    tmp = counter
    if tmp < 4 and field[posx][posy] == field[posx-1][posy-1]:
        counter += 1
        tmp = left_up_check(posx - 1,posy - 1,field,counter)
    return tmp

def upwards_check(posx:int,posy:int,field:list,counter:int=1):
    tmp = counter
    if tmp < 4 and field[posx][posy] == field[posx-1][posy]:
        counter += 1
        tmp = upwards_check(posx - 1,posy,field,counter)
    return tmp

def right_up_check(posx:int,posy:int,field:list,counter:int=1):
    tmp = counter
    if tmp < 4 and field[posx][posy] == field[posx-1][posy+1]:
        counter += 1
        tmp = right_up_check(posx - 1,posy + 1,field,counter)
    return tmp

def sideways_check(posx:int,posy:int,field:list,counter:int=1):
    tmp = counter
    if tmp < 4 and field[posx][posy] == field[posx][posy+1]:
        counter += 1
        tmp = sideways_check(posx,posy + 1,field,counter)
    return tmp

def player_turn(player_name:str):
    clear()
    print_field(field)    
    invalid_move = True
    while invalid_move:
        print("Its " + player_name +  "'s Turn")
        player_input = get_player_input()
        invalid_move = set_stone(field,player_input,player_name)
    return "4" in winner_check(field)

std_empty = "x" #standart empty field char
player_one_name = "A"
player_two_name = "B"
field = create_field()
active_player_is_one = True
# clear()
# test = [5,4,3,3,3,3]
# for i in test:
#     set_stone(field,i)
# print_field(field)

# print(winner_check(field))


while True:
    if player_turn(player_one_name):
        clear()
        print_field(field)
        print("Winner is Player one")
        break
    run(args='python ./client.py' ' "127.0.0.1"' ' 44844' '' + field)
    if player_turn(player_two_name):
        clear()
        print_field(field)
        print("Winner is player two")
        break


run(args='python ./client.py' ' "127.0.0.1"' ' 44844' 'field')