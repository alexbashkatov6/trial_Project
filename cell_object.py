from __future__ import annotations
from copy import copy, deepcopy


class CellObject:
    # def __init__(self):
    #     pass

    def copy(self) -> CellObject:
        return deepcopy(self)


class ListCO(CellObject):
    def __init__(self):
        self.lst = [0, 1, 2]


if __name__ == '__main__':

    a = ListCO()
    b = a.copy()
    a.lst = [1, 2, 3]
    print(a.lst, b.lst)

