from __future__ import annotations

from nv_typing import *
from nv_string_set_class import bounded_string_set


TypedCellState = bounded_string_set('TypedCellStates', [['empty'],
                                                        ['not_checked'],
                                                        ['checked']])


class TypedCell:

    @strictly_typed
    def __init__(self, cell_name: str, required_type: str, candidate_value: Optional[Any] = None) -> None:
        self._name = cell_name
        self._required_type = required_type
        self.candidate_value = candidate_value
        self._value = None

    @property
    def name(self):
        return self._name

    @property
    def required_type(self):
        return self._required_type

    @property
    def state(self):
        return self._state

    @property
    def value(self):
        return self._value

    @property
    def candidate_value(self):
        return self._candidate_value

    @candidate_value.setter
    def candidate_value(self, val):
        if val is None:
            self._state = TypedCellState('empty')
        else:
            self._state = TypedCellState('not_checked')
        self._candidate_value = val

    def check_candidate_value(self):
        return type_verification(self.required_type, self.candidate_value)

    def evaluate(self):
        check_result = self.check_candidate_value()
        assert check_result, 'Type check was failed'
        self._value = self.candidate_value
        self._state = TypedCellState('checked')


if __name__ == '__main__':
    @strictly_typed
    def f(asd: Callable) -> None:
        pass

    def g():
        pass

    # print(type(f))
    # print(type(TypedCell('asd', str).meth))
    # print(isinstance(f, Callable))
    # print(isinstance(TypedCell, Callable))
    # print(isinstance(TypedCell('asd', str).meth, Callable))
    # f(g)

    tc = TypedCell('tc', 'str', '13')
    print(tc.__dict__)
    print(tc.state)
    print(tc.check_candidate_value())
    print(tc.evaluate())
    print(tc.__dict__)
    print(tc.state)
    tc.candidate_value = 123
    print(tc.state)
