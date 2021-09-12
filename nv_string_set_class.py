from __future__ import annotations
from itertools import chain

from nv_typing import *


class StringSet:

    @strictly_typed
    def __init__(self, possible_eq_values_strings: list[list[str]], str_val: str) -> None:
        self.possible_strings_list = list(chain(*possible_eq_values_strings))
        assert str_val in self.possible_strings_list, 'Value should be one from {}'.format(self.possible_strings_list)
        self.eq_strings_lists = [eq_list for eq_list in possible_eq_values_strings if str_val in eq_list]
        assert len(self.eq_strings_lists) == 1, 'Value {} was found in different lists'.format(str_val)
        self.eq_strings = self.eq_strings_lists[0]
        self.value = str_val

    def __str__(self):
        return self.value

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.value)

    @strictly_typed
    def __eq__(self, other: Union[str, StringSet]) -> bool:
        if type(other) == str:
            return other in self.eq_strings
        else:
            assert self.__class__ == other.__class__, 'Classes of objects not equal'
            return other.value in self.eq_strings

    def __hash__(self):
        return hash(self.value)


if __name__ == '__main__':
    class End(StringSet):

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
    print(end_1 == End('nd'))
    print(end_1.is_negative_down)
