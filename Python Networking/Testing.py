
std_empty = 'x'
player_name = 'W'

def create_field():
    field = []
    row = [std_empty for i in range(7)]
    #row = [i for i in range(7)]                     #Field only for Tests 
    for i in range(0,6):
        field.append(row[:])
    return field
field = create_field()
field[0][0] = "W"
field[0][1] = "M"
field[5][1] = "W"
field[5][5] = "M"


def print_field(field:list):
    field_to_print = color_field(field)[:]
    for i in range(0,6):
        for j in range(0,7):
            print(field_to_print[i][j],end="\t")
        print("\n")

def color_field(field:list):
    field_colored = field[:]
    for i in range(6):
        for j in range(7):
            if field_colored[i][j] == player_name:
                field_colored[i][j] = "\033[31m" + field_colored[i][j] + "\033[0m"
            if field_colored[i][j] != std_empty:
                field_colored[i][j] = "\033[32m" + field_colored[i][j] +  "\033[0m"
    return field_colored

print(field)
print_field(field)