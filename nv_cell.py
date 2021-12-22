from __future__ import annotations
import re
from copy import copy
from functools import partial

from nv_errors import CellError, TypeCellError, SyntaxCellError
from nv_bounded_string_set_class import bounded_string_set
from nv_typing import *

BSSAttribCellType = bounded_string_set('BSSAttribCellType', [['default'],
                                                             ['no_check'],
                                                             ['name'],
                                                             ['common_splitter'],
                                                             ['bool_splitter']])


class Cell:
    def __init__(self):
        self._value = None

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, val: Any):
        self._value = val


class AttribCell(Cell):

    # @strictly_typed
    def __init__(self, name: str, str_req: str = '', str_value: str = '',
                 cell_type: BSSAttribCellType = BSSAttribCellType('default')) -> None:
        super().__init__()
        self._name = name
        self._str_req = str_req
        self._str_value = str_value
        self._cell_type = cell_type
        if not str_req:
            self._cell_type = BSSAttribCellType('no_check')

        self._active = False
        self._is_suggested_value = False
        self._status_check = ''
        self._eval_buffer = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val: str):
        self._name = val

    @property
    def cell_type(self):
        return self._cell_type

    @cell_type.setter
    def cell_type(self, val: str):
        self._cell_type = val

    @property
    def str_value(self) -> str:
        return self._str_value

    @str_value.setter
    def str_value(self, val: str):
        self._str_value = val

    @property
    def str_req(self) -> str:
        return self._str_req

    @str_req.setter
    def str_req(self, val: str):
        self._str_req = val

    @property
    def is_suggested_value(self) -> bool:
        return self._is_suggested_value

    @is_suggested_value.setter
    def is_suggested_value(self, val: bool):
        self._is_suggested_value = val

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val: bool):
        self._active = val

    @property
    def status_check(self) -> str:
        return self._status_check

    @status_check.setter
    def status_check(self, val: str):
        self._status_check = val

    @property
    def eval_buffer(self) -> Any:
        return self._eval_buffer

    @eval_buffer.setter
    def eval_buffer(self, val: Any):
        self._eval_buffer = val
