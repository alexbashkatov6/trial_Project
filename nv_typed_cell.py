from __future__ import annotations

from nv_typing import *
from nv_string_set_class import bounded_string_set


# experiment_set = set()


TypedCellState = bounded_string_set('TypedCellStates', [['empty'],
                                                        ['not_checked'],
                                                        ['checked']])


class NameDescriptor:
    def __get__(self, instance, owner):
        pass

    def __set__(self, instance, value):
        pass

    # name = NameDescriptor()


class TypedCell:

    @strictly_typed
    def __init__(self, cell_name: str, required_type: type, candidate_value: Optional[Any] = None) -> None:
        self.name = cell_name
        self.required_type = required_type
        self.state = TypedCellState('empty')
        if not (candidate_value is None):
            self.value = candidate_value

    # def meth(self):
    #     pass

# tc = TypedCell(str, '123')
# print(tc.__dict__)


if __name__ == '__main__':
    @strictly_typed
    def f(asd: Callable) -> None:
        pass

    def g():
        pass

    print(type(f))
    # print(type(TypedCell('asd', str).meth))
    print(isinstance(f, Callable))
    print(isinstance(TypedCell, Callable))
    # print(isinstance(TypedCell('asd', str).meth, Callable))
    f(g)
