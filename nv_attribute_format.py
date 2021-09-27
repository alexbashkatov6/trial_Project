from __future__ import annotations
from nv_string_set_class import bounded_string_set
from nv_typing import *


BSSAttributeType = bounded_string_set('BSSAttributeType',
                                      [['title'], ['bss_splitter'], ['virtual_splitter'], ['value']])


class AttributeFormat:
    @strictly_typed
    def __init__(self, attr_type: BSSAttributeType, attr_name: str,
                 attr_value: Optional[str] = None, possible_values: Optional[Iterable[str]] = None) -> None:
        self._attr_type = attr_type
        self._attr_name = attr_name
        self._attr_value = attr_value
        self._possible_values = possible_values

    @property
    def attr_type(self):
        return self._attr_type

    @property
    def attr_name(self):
        return self._attr_name

    @property
    def attr_value(self):
        return self._attr_value

    @property
    def possible_values(self):
        return self._possible_values
