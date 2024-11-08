import os
import random
import sys
# prints the board givin as a list with nine Fields to the output
def print_board(board:list):
    print("+-------" * 3 + "+")
    print("|" + "\t|" * 3)
    print("|  " + str(board[0]) + "\t|  " + str(board[1]) + "\t|  " + str(board[2]) + "\t|")
    print("|" + "\t|" * 3)
    print("+-------" * 3 + "+")
    print("|" + "\t|" * 3)
    print("|  " + str(board[3]) + "\t|  " + str(board[4]) + "\t|  " + str(board[5]) + "\t|")
    print("|" + "\t|" * 3)
    print("+-------" * 3 + "+")
    print("|" + "\t|" * 3)
    print("|  " + str(board[6]) + "\t|  " + str(board[7]) + "\t|  " + str(board[8]) + "\t|")
    print("|" + "\t|" * 3)
    print("+-------" * 3 + "+")

# Gets a move, the Board and a Bool if it's the users Turn, playes the Move and returns True if its valid and returns False if the move is invalid
def enter_move(move,board:list,user:bool=True):
    if move == 0: sys.exit(0)               
    if move in list_of_free_fields(board,False):
        if user:
            board[move - 1] = player_short_name 
            return True   
        else:
            board[move - 1] = bot_short_name
            return True 
    else:
        print("We dont try to steal our oponents Fields")
        return False

#returns a list of all free spaces and prints them to the Output if "output" is set to True  
def list_of_free_fields(board:list,output=True):
    free = []
    for i in board:
        if i != player_short_name and i != bot_short_name:
            free.append(i)
    if output:
        print("Free spaces are: " + str(free))
    return free

#reads the move of the palyer and checks if its a valid input
def read_player_move():
    while True:
        try:
            move = int(input("PLease enter a valid input (1-9) ATTENTION: 0 terminates the Programm \n\t - "))
            if -1 < move < 10:
                return move
        except:
            pass
        print("Wrong Input :(")

def winner_check(board:list):
    counter = 1
    winner = None
    for i in range(0,7):
        if i in [0,3,6]:
            if board[i] == board [i + 1] == board[i + 2]:
                if board[i] == bot_short_name:
                    winner = "BOT"
                elif board[i] == player_short_name:
                    winner = "Player"
                else:
                    return None
        try:
            if board[i] == board[i + 3] == board[i + 6]:
                if board[i] == bot_short_name:
                    winner = "BOT"
                elif board[i] == player_short_name:
                    winner = "Player"
                else:
                    return None
        except:
            pass
        if i == 0:
            if board[i] == board[i + 4] == board[i + 8]:
                if board[i] == bot_short_name:
                    winner = "BOT"
                elif board[i] == player_short_name:
                    winner = "Player"
                else:
                    return None
        if i == 2:
            if board[i] == board[i + 2] == board[i + 4]:
                if board[i] == bot_short_name:
                    winner = "BOT"
                elif board[i] == player_short_name:
                    winner = "Player"
                else:
                    return None
    if len(list_of_free_fields(board,False)) < 1:
        return "Unentschieden"
    return winner    
    print("Irgendwer hat gewonnen oder nicht")
    sys.exit(0)

def pc_zug(board:list):
    tmp = []
    nati = []                               #like tmp but crazy name lol
    boardtest = board[:]
    for i in list_of_free_fields(board,False):
        boardtest = board[:]   
        boardtest[i-1] = bot_short_name
        tmp.append(winner_check(boardtest))
    for i in list_of_free_fields(board,False):
        boardtest = board[:]   
        boardtest[i-1] = player_short_name
        nati.append(winner_check(boardtest))
    if 'BOT' in tmp:
        return list_of_free_fields(board)[(tmp.index('BOT'))]
    elif 'Player' in nati:
        return list_of_free_fields(board)[(nati.index('Player'))]
    else:
        return random.choice(list_of_free_fields(board,False))

def check(board:list):
    os.system('cls' if os.name =='nt' else 'clear')
    if winner_check(board) != None:
        print_board(board)
        print("Der Sieger ist: " + winner_check(board))
        return True
    return False

def pre_game():
    pregame = True 
    global player_short_name 
    player_short_name = "O"
    global bot_short_name
    bot_short_name = "X"
    os.system('cls' if os.name =='nt' else 'clear')
    while pregame:
        player_short_name = input("Short name for the player (max 4 Buchstaben): - ")
        if len(player_short_name) > 4:
            print("Short name to LONG ... Try again")
        else:
            pregame = False
        bot_short_name = input("Short name for Bot (max 4 Buchstaben): - ")
        if len(bot_short_name) > 4 or player_short_name == bot_short_name:
            print("Short name to LONG or same as player name... Try again")
        else:
            pregame = False

def game():
    os.system('cls' if os.name =='nt' else 'clear')
    game_active = True
    board = [1,2,3,4,5,6,7,8,9]
    #enter_move(5,board,False)
    enter_move(pc_zug(board),board,False)
    while game_active:
        print_board(board)
        invalid_input = True
        while invalid_input:
            list_of_free_fields(board)
            user_input = read_player_move()
            invalid_input = not enter_move(user_input,board)
        if check(board):break
        pc_move = pc_zug(board) #random.choice(list_of_free_fields(board,False))
        enter_move(pc_move,board,False)
        if check(board):break
            
pre_game()
game()
while True: 
    answer = input("wanna play again? (y/n): - ")
    if answer.lower() in ['y','j','yes']:
        game()
    elif answer.lower() in ['x','n','no']:
        sys.exit(0)
    else:
        print("Please select a valid answer")