class Card:
    def __init__(self,value:int,color:int,symbol:str): #value = value of the card: jack = 11, queen = 12 etc. color =  symbol of card: 1 = spade, 2 =  heard, 3 = diamond, 4 = clubs
        self.value = value
        self.color = color
        self.symbol = symbol
    
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
    print("Lol")
    


def flush_check(hand:list,field:list):
    counter = 1
    if hand[0].color == hand[1].color:
        counter +=1
        for i in range(len(field)):
            if hand[0].color == field[i].color:
                counter +=1
    else:
        tmp = 1
        for i in range(len(field)):
            if hand[0].color == field[i].color:
                tmp +=1
        for i in range(len(field)):
            if hand[1].color == field[i].color:
                counter +=1
        if tmp > counter:
            counter = tmp
    if counter >= 5:
        return True
    else:
        return False

def straight_check(hand:list,field:list):
    counter = 1
    if hand[0].value == hand[1].value:
        counter +=1
        if hand[1].value == field[0].value:
            counter +=1
        for i in range(len(field) - 1):
            if field[i] == field[i + 1]:
                counter += 1
    field.sort(key=lambda Card:Card.value)

def flush_helper(liste:list,start:int = 0):
    counter = 0
    if liste[start].value == liste[start + 1].value - 1:        
        counter +=1
        if start < len(liste) - 1:
            counter += flush_helper(liste,start + 1)
    return counter
       

t = create_deck()
händlich = [t.get('2'),t.get('5'),t.get('4'),t.get('3'),t.get('6')]
händlich.sort(key=lambda Card:Card.value)

print(flush_helper(händlich))

#for i in range(5):
    #print(str(händlich[i].value),händlich[i].symbol)


#print(flush_check([t.get('2'),t.get('3')],[t.get('4'),t.get('5'),t.get('6')]))
