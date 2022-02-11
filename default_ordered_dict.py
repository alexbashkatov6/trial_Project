from collections import OrderedDict
from typing import Type


class DefaultOrderedDict(OrderedDict):
    def __init__(self, default_type: Type):
        super().__init__()
        self.default_type = default_type

    def __getitem__(self, key):
        if key not in self.keys():
            self[key] = self.default_type()
        return super().__getitem__(key)
