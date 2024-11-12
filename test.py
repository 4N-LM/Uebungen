def info(string):
    print(
        "[\033[32m i \033[0m] {}".format(string)
    )
a = "\033[32m HUI \033[0m "
def test():
    print(a)
    
test()