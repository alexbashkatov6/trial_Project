from __future__ import annotations
from typing import Union
from collections.abc import Iterable
from copy import copy


class PossibleValuesDescriptor:

    def __get__(self, instance, owner):
        if not hasattr(owner, "_possible_values"):
            owner._possible_values = [item for item in owner.__dict__ if not item.startswith("__")]
        return owner._possible_values

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class ReversedValuesDescriptor:

    def __get__(self, instance, owner):
        if not hasattr(owner, "_reversed_dict"):
            owner._reversed_dict = {}
            for pv in owner.possible_values:
                int_val = owner.__dict__[pv]
                if int_val not in owner._reversed_dict:
                    owner._reversed_dict[int_val] = set()
                owner._reversed_dict[int_val].add(pv)
        return {key: copy(val) for key, val in owner._reversed_dict.items()}

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class CustomEnum:
    possible_values = PossibleValuesDescriptor()
    reversed_dict = ReversedValuesDescriptor()

    def __init__(self, value: Union[str, int]):
        if type(value) == str:
            assert value in self.__class__.possible_values, "Str value {} not possible".format(value)
            self.str_value = value
            self.int_value = self.__class__.__dict__[value]
        elif type(value) == int:
            assert value in self.__class__.reversed_dict, "Int value {} not possible".format(value)
            self.str_value = self.__class__.reversed_dict[value].pop()
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

    def are_in(self, coll: Iterable):
        return any([self == elm for elm in coll])
