from __future__ import annotations
from typing import Any
from strictly_typed import strictly_typed
from collections.abc import Iterable


class PGContent:

    def __init__(self):
        self._content = dict(default=None)

    def __repr__(self):
        return repr(self._content['default'])

    def __getitem__(self, content_key: str = 'default'):
        return self._content[content_key]

    def __setitem__(self, content_key: str = 'default', value: Any = None):
        self._content[content_key] = value

    def keys(self):
        return self._content.keys()

    def is_complex_key(self, content_key: str = 'default'):
        if issubclass(type(self[content_key]), Iterable):
            for item in self[content_key]:
                if type(item) == PolarGraph:
                    return True
        else:
            if type(self[content_key]) == PolarGraph:
                return True
        return False

    def is_complex(self):
        for content_key in self.keys():
            if self.is_complex_key(content_key):
                return True
        return False

    def add(self, content_key: str = 'default', value: Any = None):
        # not implemented yet
        pass


class PGMoves:

    def __init__(self):
        self.moves = set()
        self.active_move = None
        self.active_auto_determined = True
        self.banned_moves = set()


class PGLink:

    def __init__(self, end_positive_up, end_negative_down):
        self._ends = (end_positive_up, end_negative_down)

    @property
    def ends(self):
        return self._ends

    @ends.setter
    @strictly_typed
    def ends(self, ends_tuple: tuple) -> None:
        assert len(ends_tuple) == 2
        assert all(map(lambda x: isinstance(x, PolarGraph), ends_tuple))
        self._ends = ends_tuple


class PolarGraph:

    def __init__(self):
        self.content = PGContent()
        self._links_positive_up = set()
        self._links_negative_down = set()
        self.moves = PGMoves()

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
            link = PGLink(pg, self)
            self._links_negative_down.add(link)
            pg._links_positive_up.add(link)
        else:
            link = PGLink(self, pg)
            self._links_positive_up.add(link)
            pg._links_negative_down.add(link)


