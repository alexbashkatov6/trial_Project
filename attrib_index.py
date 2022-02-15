from typing import Union


class CompositeAttributeIndex:
    def __init__(self, indexes: list[Union[str, int]] = None):
        if not indexes:
            self.indexes = []
        else:
            self.indexes = indexes

    def append(self, item: Union[str, int]):
        self.indexes.append(item)

    def last_array(self) -> int:
        if self.indexes and isinstance(self.indexes[-1], int):
            return self.indexes[-1]
        return -1
