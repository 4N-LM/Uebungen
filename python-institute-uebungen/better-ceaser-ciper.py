line = input("input your line to be encrypted: ")
while True:
    try:
        shift_value = int(input("Enter your personal shift value: "))
        break
    except:
        print("Not a valid input")

enc_str = ''
for char in line:
    if not char.isalpha():
        enc_str += char    
    if char.isupper():
        if ord(char) + shift_value > ord('Z'):
            enc_str += chr(ord('A') + (shift_value - (ord('Z') - ord(char))) - 1)
        else:
            enc_str += chr(ord(char) + shift_value)
    if char.islower():
        if ord(char) + shift_value > ord('z'):
            enc_str += chr(ord('a') + (shift_value - (ord('z') - ord(char))) - 1)
        else:
            enc_str += chr(ord(char) + shift_value)
print(line)
print(enc_str)

    

