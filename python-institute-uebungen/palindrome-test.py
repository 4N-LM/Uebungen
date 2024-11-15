input_str = input("Enter you string to be tested: ")
input_str = input_str.replace(" ","")

if input_str.isalpha():
    input_str = input_str.upper()
    string1 = input_str[:len(input_str)//2]
    string2 = input_str[len(input_str)//2:]
    string2 = string2[::-1]
    palindrom = True
    for i in range(len(string1) - 1):
        if string1[i] == string2[i]:
            continue
        else:
            palindrom = False
            print("It's not a palindrome")
            break
if palindrom:
    print("It's a palindrome")
