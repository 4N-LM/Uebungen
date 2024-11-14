
from subprocess import run 

#run(args='python ./client.py' ' "127.0.0.1"' ' 44844' ' "Hello World"')

std_empty = 'x'

def create_field():
    field = []
    row = [std_empty for i in range(7)]
    #row = [i for i in range(7)]                     #Field only for Tests 
    for i in range(0,6):
        field.append(row[:])
    return field
field = create_field()
field[2][3] = "W"
field[4][1] = "M"


def str_to_field(input_str:str):
    str_to_edit = input_str
    tmp = []
    for i in range(5):
        abc = []
        for j in range(7):
            abc.append(str_to_edit[0])
            str_to_edit = str_to_edit[1:]
        tmp.append(abc[:])
        str_to_edit = str_to_edit[1:]
    return tmp

def field_to_str(field:list):
    field_send_form2 = ""
    field_send_form = []
    for i in range(6):
        for j in range(7):
            field_send_form.append(field[i][j])
        field_send_form.append(":")

    field_send_form2 = "".join(field_send_form)
    return field_send_form2

test = field_to_str(field)
print(test)
print(str_to_field(test))