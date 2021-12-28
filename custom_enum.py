from __future__ import annotations
from typing import Union
from collections.abc import Iterable
from copy import copy


class CustomEnum:
    def __init__(self, value: Union[str, int]):
        if not hasattr(self.__class__, "possible_values"):
            self.__class__.possible_values = [item for item in self.__class__.__dict__ if not item.startswith("__")]
            self.__class__.reversed_dict = {}
            for pv in self.__class__.possible_values:
                int_val = self.__class__.__dict__[pv]
                if int_val not in self.__class__.reversed_dict:
                    self.__class__.reversed_dict[int_val] = set()
                self.__class__.reversed_dict[int_val].add(pv)
        if type(value) == str:
            assert value in self.__class__.possible_values, "Str value {} not possible".format(value)
            self.str_value = value
            self.int_value = self.__class__.__dict__[value]
        elif type(value) == int:
            assert value in self.__class__.reversed_dict, "Int value {} not possible".format(value)
            self.str_value = copy(self.__class__.reversed_dict[value]).pop()
            self.int_value = value

    def __repr__(self):
        return '{}("{}")'.format(self.__class__.__name__, self.str_value)

    __str__ = __repr__

    def __eq__(self, other):
        assert type(other) in [int, str, self.__class__], "Only str or class supported for comparison"
        if type(other) == str:
            return other in self.__class__.reversed_dict[self.int_value]
        elif type(other) == int:
            return self.int_value == other
        else:
            return self.int_value == other.int_value

    def are_in(self, c: Iterable):
        return any([self == en for en in c])
