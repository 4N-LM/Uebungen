
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
field_send_form2 = ""

field_send_form = []
for i in range(6):
    for j in range(7):
        field_send_form.append(field[i][j])
    field_send_form.append(":")

field_send_form2 = "".join(field_send_form)
run(args='python ./client.py' ' "127.0.0.1"' ' 44844' ' ' + field_send_form2)