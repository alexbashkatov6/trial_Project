from collections import OrderedDict
from itertools import combinations
print(2 - True - True)
print({1,2} & {3,2})
a = ["n", "l", "n", "l", "n", "l1", "n1"]
b = ["n"]
print(a[::2])
print(a[1::2])
print(b[::2])
print(b[1::2])
print(a[-2:])
print(tuple(a[-2:]))
# a.
# c, d = b[-2:]
# print(c, d)
# print(set(None))

f = OrderedDict({1:"1"})
for i in range(10):
    f[i] = str(i)
print(f)
print(list(f.keys())[-1])
# f.keys().
print(a[:-2])
print(a[:-1])
p = {2,1}
q = {3, 2}
p|=q
print(p)
print(p|q)
print([i for i in combinations({1,2,3}, 2)])

a = {1: "1", 2: "2"}
b = {3: "3", 4: "4"}
a.update(b)
print(a)
g = {1,2}
# g|= [2, 3]
print(g)
for i in range(1):
    print("hello")
print(0 in {})
class A:
    a = 0
    def __init__(self):
        pass
        # self.a = 1
p = A()
print(p.a)


def fun(x):
    return x+1


print(list(map(fun, (0, 1, 2, 3))))


class MyDescriptor:

    def __set_name__(self, owner, name):
        print('Атрибут %s' % name)


class MyClass:
    field1 = MyDescriptor()
    field2 = MyDescriptor()


a = [1, 2, 3]
b = [*a, 4, 5]
print(b)

# eval(int("sdsd"))
from typing import Type
print(isinstance(list[str], Type))

a = [1, 2, 3, [4]]
print(4 in a)
