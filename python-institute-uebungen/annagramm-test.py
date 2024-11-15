input_str1 = input("Enter your first line: ")
input_str2 = input("Enter your second line: ")
input_str1 = input_str1.replace(" ","")
input_str2 = input_str2.replace(" ","")

if input_str1.isalpha() and input_str2.isalpha():
    input_str1 = sorted(input_str1.lower())
    input_str2 = sorted(input_str2.lower())
    if input_str1 == input_str2:
        print("Anagrams")
    else:
        print("Not anagrams")

