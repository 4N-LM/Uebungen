import random

random.seed()
i = 20
while i > 0:
    print (int(round((random.random() * 10),0)))
    i -= 1