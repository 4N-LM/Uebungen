import sys
sys.setrecursionlimit(100000)
def test(num,i = 2):
    premium = False
    print("Test mit Nummer: " + str(i))
    if num % i == 0:
        return False
    elif i < (num/2)+1:
        premium = test(num,i+1)
    else:
        premium = True
    return premium

#print(test(10007))

#for i in range(1, 20):
#	if is_prime(i + 1):
#			print(i + 1, end=" ")


def test_prime(num):
    for i in range(2,(num//2)+2):
        if num % i ==0:
            return None
    return num
    
j = []
for i in range(100_000_00,100_002_00):
   premiumm = test_prime(i)
   if premiumm != None:
       j.append(premiumm)

print (j)