from __future__ import annotations
from itertools import chain
from copy import copy
# from abc import ABCMeta

from nv_typing import *


class BoundedStringSet:  # metaclass=ABCMeta
    def __init__(self, str_val: str = None):
        if str_val:
            self.value = str_val

    def __str__(self):
        return self.value

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.value)

    @strictly_typed
    def __eq__(self, other: Union[str, BoundedStringSet]) -> bool:
        if type(other) == str:
            return other in self.eq_strings
        else:
            assert self.__class__ == other.__class__, 'Classes of objects not equal'
            return other.value in self.eq_strings

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(id(self))

    @property
    def eq_strings(self) -> list[str]:
        return self._eq_strings

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, str_val: str) -> None:
        assert str_val in self.possible_strings, \
            'Value should be one from {}'.format(self.possible_strings)
        _eq_strings_lists = [eq_list for eq_list in self.eq_value_groups if str_val in eq_list]
        assert len(_eq_strings_lists) == 1, 'Value {} was found in different lists'.format(str_val)
        self._eq_strings = list(_eq_strings_lists[0])
        self._value = str_val


class CopyDescriptor:

    def __init__(self, given_iterable):
        self.given_iterable = given_iterable

    def __get__(self, instance, owner=None):
        return copy(self.given_iterable)


@strictly_typed
def bounded_string_set(type_name: str, eq_value_groups: Iterable[Iterable[str]],
                       additional_base_classes: Optional[Union[type, Iterable[type]]] = None) -> type:
    possible_strings = list(chain(*eq_value_groups))
    unique_values = [list(eq_values)[0] for eq_values in eq_value_groups]
    base_classes = (BoundedStringSet,)
    if additional_base_classes is None:
        pass
    elif type(additional_base_classes) == type:
        base_classes = (*base_classes, additional_base_classes)
    else:
        base_classes = (*base_classes, *set(additional_base_classes))
    new_type = type(type_name, base_classes,
                    {'eq_value_groups': CopyDescriptor(eq_value_groups),
                     'possible_strings': CopyDescriptor(possible_strings),
                     'unique_values': CopyDescriptor(unique_values)})
    return new_type


if __name__ == '__main__':

    NoFunctionalityEnd = bounded_string_set('NoFunctionalityEnd', [['negative_down', 'nd'], ['positive_up', 'pu']])


    class End(NoFunctionalityEnd):

        @property
        @strictly_typed
        def is_negative_down(self) -> bool:
            return self == 'nd'

        @property
        @strictly_typed
        def is_positive_up(self) -> bool:
            return self == 'pu'

        @property
        @strictly_typed
        def opposite_end(self) -> End:
            if self.is_negative_down:
                return End('pu')
            else:
                return End('nd')


    end = End('pu')
    print([end.opposite_end], end.is_negative_down, end.is_positive_up)

    # CoolClass = bounded_string_set('CoolClass', [['negative_down', 'nd'], ['positive_up', 'pu']])
    # print(CoolClass.__dict__)
    # cc = CoolClass('pu')
    # print(cc.__dict__)
    # print(cc.str_value, cc.eq_strings)
    bss = BoundedStringSet()
    print(isinstance('nd', End))
