from __future__ import annotations
from itertools import chain
from collections.abc import Iterable

from nv_typing import *


class BoundedStringSet:

    @strictly_typed
    def __init__(self, possible_eq_values_strings: Iterable[Iterable[str]], str_val: str = None) -> None:
        self._possible_eq_values_strings = possible_eq_values_strings
        self._possible_strings_list = list(chain(*possible_eq_values_strings))
        if str_val:
            self.value = str_val

    def __str__(self):
        return self.value

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.value)

    @strictly_typed
    def __eq__(self, other: Union[str, BoundedStringSet]) -> bool:
        if type(other) == str:
            # print('in eq ', self, self.eq_strings)
            return other in self.eq_strings
        else:
            assert self.__class__ == other.__class__, 'Classes of objects not equal'
            return other.value in self.eq_strings

    def __hash__(self):
        return hash(self.value)

    @property
    def possible_strings_list(self) -> list[str]:
        return self._possible_strings_list

    @property
    def eq_strings(self) -> list[str]:
        return self._eq_strings

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, str_val: str) -> None:
        assert str_val in self._possible_strings_list, \
            'Value should be one from {}'.format(self._possible_strings_list)
        self._eq_strings_lists = [eq_list for eq_list in self._possible_eq_values_strings if str_val in eq_list]
        assert len(self._eq_strings_lists) == 1, 'Value {} was found in different lists'.format(str_val)
        self._eq_strings = list(self._eq_strings_lists[0])
        self._value = str_val


class BoundedStringDict:

    def __init__(self, keys: Optional[Iterable[str]] = None) -> None:
        self._storage_dict = {}
        self._possible_keys = set()
        if keys:
            self.register_keys(keys)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self._storage_dict)

    def __getitem__(self, item: str):
        self.check_possibility(item)
        return self._storage_dict[item]

    def __setitem__(self, key: str, value: Any):
        self.check_possibility(key)
        self._storage_dict[key] = value

    def check_possibility(self, item: str):
        assert item in self.possible_keys, 'Key {} not in possible set {}'.format(item, self.possible_keys)

    @property
    def possible_keys(self):
        return self._possible_keys

    def register_key(self, key: str):
        self._possible_keys.add(key)
        self._storage_dict[key] = None

    def register_keys(self, keys: Iterable[str]):
        for key in keys:
            self.register_key(key)

    @property
    def storage_dict(self):
        return self._storage_dict


if __name__ == '__main__':
    class End(BoundedStringSet):

        @strictly_typed
        def __init__(self, str_end: str) -> None:
            super().__init__([['negative_down', 'nd'], ['positive_up', 'pu']], str_end)

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


    end_1 = End('negative_down')
    # print(end_1 == End('nd'))
    # print(end_1.is_negative_down)

    bsd = BoundedStringDict(['a', 'b', 'c'])
    bsd['a'] = 123
    bsd.register_key('d')
    bsd.register_keys(['e', 'f', 'g'])
    bsd['d'] = 46
    bsd['g'] = 89
    print(bsd)
