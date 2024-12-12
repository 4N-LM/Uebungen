from random import randint
class Card:
    def __init__(self,value:int,color:int,symbol:str,active:bool=False): #value = value of the card: jack = 11, queen = 12 etc. color =  symbol of card: 1 = spade, 2 =  heard, 3 = diamond, 4 = clubs
        self.value = value
        self.color = color
        self.symbol = symbol
        self.active = active
    
    def __str__(self):
        return 'Value: ' + str(self.value) + ' Color: ' + str(self.color) + ' Symbol: '  + self.symbol 

def create_deck():
    tmp = []
    deck = {}
    i = 1
    for c in range(1,5):                        #create a list of all cards based of Unicode Order
        for v in range(1,17):
            unicode_char = chr(0x1F0A0 + i)
            tmp.append(Card(v,c,unicode_char)) 
            i+=1

    tmp2 = []
    for i in range(len(tmp)):                   #removing all unwanted cards from the list
        if i not in [11,14,15,27,30,31,43,46,47,59,62,63]:
            tmp2.append(tmp[i])
    tmp = tmp2[:]

    for i in range(len(tmp)):                   # fixing wrong value for Ace, Queen and King
        if tmp[i].value == 13:
            tmp[i].value = 12

        if tmp[i].value == 14:
            tmp[i].value = 13

        if tmp[i].value == 1:
            tmp[i].value = 14

    for i in range(len(tmp)):                   #converting list into a Dictonary
            deck[str(i + 1)] = tmp[i]
         
    return deck

def royal_flush_check(hand:list,field:list):
    tmp = hand + field
    print(type(tmp))
    tmp.sort(key=lambda Card:Card.value)
    symbols = []
    for i in tmp:
        symbols.append(i.symbol)
    a = ['🂪','🂫','🂭','🂮','🂡']
    b = ['🂺','🂻','🂽','🂾','🂱']
    c = ['🃊','🃋','🃍','🃎','🃁']
    d = ['🃚','🃛','🃝','🃞','🃑']
    if set(a).issubset(symbols) or set(b).issubset(symbols) or set(c).issubset(symbols) or set(d).issubset(symbols): 
        print('Royal Flush!!')
        return True
    return False

def FullHouse(hand:list,field:list):
    x = any_of_a_kind(3,hand,field)
    y = any_of_a_kind(2,hand,field)
    if x[0][0] and y[0][0]:
        if x[0][2] != y[0][2] or  x[0][2] != y[1][2] or x[1][2] != y[0][2] or x[1][2] != y[1][2] or x[0][2] != y[2][2]:
            if y[0][2] < y[1][2]:
                y[0] = y[1]           
            return (True, x[0][2], y[0][2])
    return (False,)

def flush_check(hand:list,field:list,output:bool=True):          #noch verbessern über sortierte liste statt einzeln!!
    counter = 1
    if hand[0].color == hand[1].color:
        counter +=1
        for i in range(len(field)):
            if hand[0].color == field[i].color:
                counter +=1
        x = hand[0].value
        if hand[0].value < hand[1].value:
            x = hand[1].value
        counter = (counter,x)
    else:
        tmp = 1
        for i in range(len(field)):
            if hand[0].color == field[i].color:
                tmp +=1
        tmp = (tmp,hand[0].value)
        for i in range(len(field)):
            if hand[1].color == field[i].color:
                counter +=1
        counter = (counter,hand[1].value)
        if tmp[0] > counter[0]:
            counter = tmp
    if counter >= 5:
        return True
    else:
        return False 

def straight_check(hand:list,field:list):
    try_straight = hand + field     
    try_straight = list(set(try_straight))
    try_straight.sort(key=lambda Card:Card.value)
    unique_list = []
    seen_y_values = set()
    for obj in try_straight:
        if obj.value not in seen_y_values:
            unique_list.append(obj)
            seen_y_values.add(obj.value)      
    try_straight = unique_list[:]
   
    counter = straight_helper(try_straight)
    if counter[0] > 4:
        print("Straight!")
        return (True,counter[1])
    else:
        return (False,)

def straight_helper(liste:list):
    counter = 1
    tmp = []
    for i in range(len(liste)):
        try:
            if liste[i].value == liste[i+1].value - 1:
                counter +=1
            else:                
                counter = 1
        except:
            pass 
        finally:
            print(counter)
            tmp.append((counter,liste[i].value + 1)) #Value + 1 because starighthelper cant give you the highest of a Staright else
    print(tmp)
    return max(tmp,key=lambda tmp:tmp[0])

def card_list_to_string(card_list:list):
    tmp = ''
    for i in range(len(card_list)):
        tmp += str(card_list[i].value)
        tmp += '\t'
    return tmp

def straight_flush_check(hand:list,field:list):
    x = straight_check(hand,field)

    if x[0] and flush_check(hand[:],field[:]):
        print('Straight Flush!')
        return True
    else:
        return False

def twoPair(hand:list,field:list):
    x = any_of_a_kind(2,hand,field)
    if len(x) > 1 :
        return True
    return False

def any_of_a_kind(how_much_of_a_kind:int,hand:list,field:list):
    another_list = hand + field
    another_list.sort(key=lambda Card:Card.value)
    tmp = []
    for i in range(1, 15):
        try:
            count = sum(1 for card in another_list if card.value == i)
            tmp.append((count, i))
        except Exception as e:
            print('Fehler: ' + str(e))
        
    tmptmp = []
    for i in tmp:
        if i[0] == how_much_of_a_kind:
            tmptmp.append((True,) + i)
    if len(tmptmp) > 0 :
        return tmptmp
    else:
        return [(False,)]    

def createHand(listeee:list):
    tmp = []
    for i in range(2):
        tmp.append(kartenspiel.get(str(listeee[i])))
        print(f'Hand {i} ' + str(kartenspiel.get(str(listeee[i]))))
    return tmp[:]
        
def createTable(listeeee:list):
    tmp = []
    for i in range(len(listeeee)):
        tmp.append(kartenspiel.get(str(listeeee[i])))
        print(f'Table {i} ' + str(kartenspiel.get(str(listeeee[i])).symbol))
    return tmp[:]

def StringToList(eingang:str):
    tmp = []
    for i in eingang:
        tmp.append(i)
    return tmp

def highestCheck(hand,table):
    if type(hand) == str:
        hand = StringToList(hand)
    if type(table) == str:
        table = StringToList(table)
    print('Hand: ' + str(hand))
    print('Table: ' + str(table))


    print('Royal') #######
    if royal_flush_check(hand,table):
        return (10,None,None)
    print('StraightFlush')######
    if straight_flush_check(hand,table):
        return 9
    
    print('4 of a ')
    x = any_of_a_kind(4,hand,table) 
    if x[0][0]:
        return (8,x[0][2],15)
    
    print('Full House')
    x = FullHouse(hand,table) 
    if x[0]:
        return (7,x[1],x[2])
    
    print('Flush')######
    if flush_check(hand,table,False):
        return 6
    
    print('straight')######
    x = straight_check(hand,table) 
    if x[0]:
        return (5,x[1],15)
        
    print('3 of a ')#####
    if any_of_a_kind(3,hand,table)[0][0]:
        return 4
    
    if twoPair(hand,table):
        return 3
    
    if any_of_a_kind(2,hand,table)[0][0]:
        return 2
    return 1

if __name__ == '__main__':
    kartenspiel = create_deck()
    x = createHand([1,14])
    y = createTable([28,29,30,31,32,34,35,37])
    print(straight_helper(y))
    print(any_of_a_kind(4,x,y))
    