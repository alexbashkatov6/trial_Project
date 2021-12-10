import math
import numpy as np


def my_func(*args, **kwargs):
    print(len(args))
    print(kwargs.pop('h'))


my_func(4, 6, 9, h=6)

a = np.array([[1, 2], [3, 4]])
b = np.linalg.inv(a)
print(b)
print(np.dot(a, b))
print(a[0][1])
