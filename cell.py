from __future__ import annotations
# from copy import copy


class Cell:
    def __init__(self, element, obj=None):  # : element = Union[PolarNode, PGLink, PGMove], obj = Any
        self._element = element
        self._obj = obj

    @property
    def element(self):
        return self._element

    @property
    def obj(self):
        return self._obj

    @obj.setter
    def obj(self, val):
        self._obj = val
