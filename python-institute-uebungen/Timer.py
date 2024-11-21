
class Timer:
    def __init__(self,hour:int=0,min:int=0,sec:int=0 ):
        self.time = (hour*3600) + (min*60) + sec 

    def format_str(self,unformatet:str):
        if len(unformatet) == 1:
            formated = '0' + unformatet
        else:
            formated = unformatet
        return formated

    def __str__(self):
        return self.format_str(str(self.time//3600)) + ':' + self.format_str(str((self.time%3600)//60)) + ':' + self.format_str(str((self.time%3600)%60))

    def next_second(self):
        if self.time == 86399:
            self.time = 0
        else:
            self.time += 1

    def prev_second(self):
        if self.time == 0:
            self.time = 86399
        else:
            self.time -= 1


timer = Timer(23, 59, 59)
print(timer)
for i in range (50):
    timer.next_second()
print(timer)
timer.prev_second()
print(timer)
