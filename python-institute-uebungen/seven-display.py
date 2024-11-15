zeichen = ['###','#  ','  #','# #']
zahlen = [[0,3,3,3,0],[2,2,2,2,2],[0,2,0,1,0],[0,2,0,2,0],[3,3,0,2,2],[0,1,0,2,0],[0,1,0,3,0],[0,2,2,2,2],[0,3,0,3,0],[0,3,0,2,0]]
def print_number(num:int):
    s = ""
    for i in range(5):
        for j in str(num):
            s +=zeichen[zahlen[int(j)][i]]
            s += " "
        s += "\n"
    print(s)

number = int(input("Enter a positive number - "))
print_number(number)