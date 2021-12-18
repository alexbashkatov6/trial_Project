from __future__ import annotations
from nv_bounded_string_set_class import bounded_string_set
from nv_typing import *


BSSAttributeType = bounded_string_set('BSSAttributeType',
                                      [['title'], ['splitter'], ['form']])


class AttributeFormat:
    @strictly_typed
    def __init__(self, attr_type: BSSAttributeType, attr_name: str,
                 attr_value: str = '', possible_values: Optional[Iterable[str]] = None) -> None:
        self._attr_type = attr_type
        self._attr_name = attr_name
        self._attr_value = attr_value
        self._possible_values = possible_values
        self._status_check = ''
        self._req_type_str = ''
        self._is_suggested = False

    def __repr__(self):
        return '{}({}, {}, {}, {})'.format(self.__class__.__name__, self.attr_type, self.attr_name,
                                           self.attr_value, self.status_check)

    @property
    def attr_type(self):
        return self._attr_type

    @property
    def attr_name(self):
        return self._attr_name

    @property
    def attr_value(self):
        return self._attr_value

    @attr_value.setter
    def attr_value(self, val):
        self._attr_value = val

    @property
    def possible_values(self):
        return self._possible_values

    @property
    def status_check(self):
        return self._status_check

    @status_check.setter
    def status_check(self, val: str):
        self._status_check = val

    @property
    def is_suggested(self):
        return self._is_suggested

    @is_suggested.setter
    def is_suggested(self, val: bool):
        self._is_suggested = val

    @property
    def req_type_str(self):
        return self._req_type_str

    @req_type_str.setter
    def req_type_str(self, val: str):
        self._req_type_str = val
