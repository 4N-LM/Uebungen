while True:
    date = input("please enter your Birthday in a 8 letter long format:\n - ")
    if len(date) != 8 or not date.isnumeric:
        print("wrong input try again...")
    else:
        break

def sum_all(number:str):
    tmp = 0
    for i in number:
        tmp += int(i)
    if len(str(tmp)) > 1:
        tmp = sum_all(str(tmp))
    return tmp

print("Your Digit of Life is: " + str(sum_all(date)))    