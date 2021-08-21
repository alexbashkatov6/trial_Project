from __future__ import annotations
from typing import Any
from strictly_typed import strictly_typed


class PolarGraph:

    def __init__(self):
        self._content = None
        self._links_positive_up = set()
        self._links_negative_down = set()

    @property
    def content(self) -> Any:
        return self._content

    @content.setter
    def content(self, value: Any):
        self._content = value

    @property
    def links_positive_up(self) -> set:
        return self._links_positive_up

    @property
    def links_negative_down(self) -> set:
        return self._links_negative_down

    @strictly_typed
    def pg_connect(self, pg: PolarGraph, end: str = 'negative_down') -> None:
        assert end in ['negative_down', 'positive_up'], 'end should be negative_down or positive_up'
        if end == 'negative_down':
            self._links_negative_down.add(pg)
            # pg._links_positive_up.add(self)
        else:
            self._links_positive_up.add(pg)
            # pg._links_negative_down.add(self)

print('PolarGraph' in globals())

pg_1 =  PolarGraph()
pg_2 =  PolarGraph()
pg_1.pg_connect(pg_2)

