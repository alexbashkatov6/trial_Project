from __future__ import annotations
from copy import copy, deepcopy


class CellObject:

    def copy(self) -> CellObject:
        return deepcopy(self)


class ListCO(CellObject):
    def __init__(self):
        self.lst = [0, 1, 2]


class Example:
    pass


if __name__ == '__main__':

    a = ListCO()
    e1 = Example()
    e2 = Example()
    e3 = Example()
    a.lst = [e1, e2, e3]
    b = a.copy()
    print(a.lst)
    print(b.lst)


