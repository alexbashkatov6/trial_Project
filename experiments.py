from collections import Counter, defaultdict, OrderedDict
from typing import Optional, Type

c = Counter(["odin", "dva", "tri", "dva", "tri", "tri"])
print(dict(c))
# a=2
for a in range(5):
    if 1<a<3:
        print("ok", a)
b = [1 ,2 ,3,4,5,6,7,8]
print(b[b.index(2):b.index(5)+1])
print(type(abs(2-1)))
print(set([1,2,3]) == set([1,2,3]))

c=[1]
print(c[1:])
# a = defaultdict(Or)


class DefaultOrderedDict(OrderedDict):
    def __init__(self, default_type: Type):
        super().__init__()
        self.default_type = default_type

    def __getitem__(self, key):
        if key not in self.keys():
            # super().__setitem__(key, self.default_type())
            self[key] = self.default_type()
        return super().__getitem__(key)


dodict = DefaultOrderedDict(OrderedDict)
dodict["lala"]["tata"] = "ads"
print(dodict["lala"])

s = "abc"
s = s[:s.index("b")+1]
print(s)

a = 0

try:
    a = 1
    2/0
except ZeroDivisionError:
    print(ZeroDivisionError)
print(a)


class MyException(Exception):
    pass


try:
    raise MyException("first", "second")
except MyException as e:
    print("MyException!", e.args[0], e.args[1])

print(s[:2])

print(", ".join(["1", "2", "3"]))
i = 1_0000_00
print(type(i))
# import sys
# next(sys.stdin)
# sys.argv[0]
# s = ""
# s << "a" << "b"
# print(s)
print("aaa".replace("a", "b"))
od = OrderedDict([(1,"1"), (2, "2")])
print(od)
p = list(od.keys())
q = od.keys()
print(p, q)
od.pop(1)
print(p, q)
print(len(od))
