class A:
    pass


a = A()
a.qwe = 7

setattr(a, 'qwe', 5)
print(a.__dict__)
