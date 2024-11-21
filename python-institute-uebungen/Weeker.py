class WeekDayError(Exception):
    pass
	

class Weeker:
    #
    # Write code here.
    #

    def __init__(self, day):
        self.dotw = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        if not day in self.dotw:
            raise WeekDayError
        self.today = day

    def __str__(self):
        return self.today

    def add_days(self, n):
        u = [i for i,x in enumerate(self.dotw) if x == self.today][0]
        u += self.get_actual_days(n)
        self.today = self.dotw[u]

    def subtract_days(self, n):
        u = [i for i,x in enumerate(self.dotw) if x == self.today][0]
        u -= self.get_actual_days(n)
        self.today = self.dotw[u]

    def get_actual_days(self,day:int):
        if 0 < day < 8:
            return day
        else:
            return (day % 7)

try:
    weekday = Weeker('Mon')
    print(weekday)
    weekday.add_days(15)
    print(weekday)
    weekday.subtract_days(23)
    print(weekday)
    weekday = Weeker('Monday')
except WeekDayError:
    print("Sorry, I can't serve your request.")