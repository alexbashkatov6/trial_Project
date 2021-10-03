from __future__ import annotations

from nv_typing import *
from nv_bounded_string_set_class import bounded_string_set


class NamedCell:

    @strictly_typed
    def __init__(self, cell_name: str, value: Optional[Any] = None) -> None:
        self._name = cell_name
        self._value = value

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value


TypedCellState = bounded_string_set('TypedCellStates', [['not_checked'],
                                                        ['check_fail'],
                                                        ['check_status']])


class TypedCell(NamedCell):

    @strictly_typed
    def __init__(self, cell_name: str, required_type: str, candidate_value: str = '') -> None:
        super().__init__(cell_name)
        self._name = cell_name
        self._required_type = required_type
        self.candidate_value = candidate_value

    @property
    def required_type(self):
        return self._required_type

    @property
    def check_status(self) -> bool:
        return self._check_status

    @property
    def candidate_value(self):
        return self._candidate_value

    @candidate_value.setter
    def candidate_value(self, val):
        self._check_status = False
        self._candidate_value = val

    def evaluate(self, eval_function):
        self._value, self._check_status = eval_function(self.candidate_value, self.required_type)


if __name__ == '__main__':

    tc = TypedCell('tc', 'str', '13')
    print(tc.__dict__)
