from __future__ import annotations
from numbers import Number
import re

from nv_instances_control import instances_control
from nv_typing import *


class FieldCoord:
    @strictly_typed
    def __init__(self, value: Union[Number, str], cs: CoordinateSystem) -> None:
        self.value = value
        self.cs = cs

    def __repr__(self):
        return 'FieldCoord({}, {})'.format(self.value, self.cs.name)

    @property
    def value(self):
        return self._value

    @value.setter
    @strictly_typed
    def value(self, val: Union[Number, str]) -> None:
        if isinstance(val, Number):
            self._value = val
        else:
            assert re.fullmatch(r'PK_\d+\+\d+', val), 'Coord format is PK_xxxx+yyy, given {}'.format(val)
            plus_pos = val.find('+')
            self._value = int(val[3:plus_pos]) * 100 + int(val[plus_pos + 1:])

    @strictly_typed
    def __add__(self, other: Number) -> FieldCoord:
        return FieldCoord(self.value+other, self.cs)

    @strictly_typed
    def __sub__(self, other: Union[Number, FieldCoord]) -> Union[Number, FieldCoord]:
        if isinstance(other, Number):
            return FieldCoord(self.value-other, self.cs)
        else:
            assert self.cs == other.cs, \
                'Should be the same cs in sub Field coords {}, {}'.format(self, other)
            return self.value-other.value


# class BuildDescriptor:
#
#     def __get__(self, instance, owner=None):
#         if instance is None:
#             return self
#         if owner == CoordinateSystem:
#             print('owner CoordinateSystem')
#         return None


@instances_control
class CoordinateSystem:
    pass
    # build_method = BuildDescriptor()


if __name__ == '__main__':

    cs = CoordinateSystem()
    # cs.build_method
    fc = FieldCoord('PK_2+3', cs)
    fc_2 = FieldCoord('PK_1+2', cs)
    print(fc.value)
    print(fc+15)
    print(fc-15, fc-fc_2)
