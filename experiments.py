import math

def my_func(*args, **kwargs):
    print(len(args))
    print(kwargs.pop('h'))

my_func(4,6, 9, h=6)

