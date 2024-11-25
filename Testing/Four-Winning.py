import os
import sys
import client
import copy

def quit():
    clear()
    print("exiting")
    sys.exit()

def clear():
    os.system('cls' if os.name =='nt' else 'clear')

def create_field():
    field_make = []
    row = [std_empty for i in range(7)]
    #row = [i for i in range(7)]                     #Field only for Tests 
    for i in range(0,6):
        field_make.append(row[:])
    return field_make[:]

def print_field(input:list):
    color_field(input)
    for i in range(0,6):
        for j in range(0,7):
            print(input[i][j],end="\t")
        print("\n")

def color_field(input:list):
    field_colored = input[:]
    for i in range(6):
        for j in range(7):
            if field_colored[i][j] == player_name:
                field_colored[i][j] = "\033[31m" + field_colored[i][j] + "\033[0m"
            if field_colored[i][j] != std_empty:
                field_colored[i][j] = "\033[32m" + field_colored[i][j] +  "\033[0m"
    return field_colored[:]

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
    print_field(copy.deepcopy(field))    
    invalid_move = True
    while invalid_move:
        print("Its " + player_name +  "'s Turn")
        player_input = get_player_input()
        invalid_move = set_stone(field,player_input,player_name)
    return "4" in winner_check(field)

def field_to_str(field:list):
    field_send_form2 = ""
    field_send_form = []
    for i in range(6):
        for j in range(7):
            field_send_form.append(field[i][j])
        field_send_form.append(":")

    field_send_form2 = "".join(field_send_form)
    return field_send_form2

def str_to_field(input_str:str):
    str_to_edit = input_str.replace('False:', '',1)

    tmp = []
    for i in range(6):
        abc = []
        for j in range(7):
            abc.append(str_to_edit[0])
            str_to_edit = str_to_edit[1:]
        tmp.append(abc[:])
        str_to_edit = str_to_edit[1:]
    return tmp

IP = str(input("Please Enter the Server IP"))
port = int(input("Please Enter the Games port"))

if IP == "":
    IP = '127.0.0.1'
if port == "":
    port = 44844

client.init(IP,port)
player_name = "O"
std_empty = "x" #standart empty field char
while True:
    player_name = input("Input one Character long name for you: \n - ")
    if 0 > len(player_name) > 1:
        print("Wrong input")
    else:
        break
field = create_field()

first = True
i = 0
while True:
    if first:
        i += 1
        print_string = ""
        print_string += str(player_turn(player_name)) + ":"
        print_string += field_to_str(field)
        if 'True' in print_string:
            print("You are the Winenr")
            break
        client.send_data(print_string)
    
    print("Waiting for Oponends Turn")
    answer_string = client.answer()
    if 'lost' in answer_string:
        print("You have lost")
        break
    field = str_to_field(answer_string)[:]
    first = True

print(i)
client.close_connection()
  

