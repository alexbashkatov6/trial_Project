from __future__ import annotations
from nv_typing import *
from copy import copy


class PGContent:

    def __init__(self):
        # content 'whole' is simple object, other keys for consistent from PG
        self._content = dict(whole=None)

    def __repr__(self):
        return repr(self._content['whole'])

    def __getitem__(self, content_key: str = 'whole'):
        return self._content[content_key]

    def __setitem__(self, content_key: str = 'whole', value: Any = None):
        self._content[content_key] = value

    def keys(self):
        return self._content.keys()


class PGMovesGroup:

    def __init__(self):
        self._moves = set()
        self._group_policy = 'synchronize'

    @property
    def moves(self):
        return copy(self._moves)

    @property
    def active_moves(self):
        return set(filter(lambda item: item.active, self._moves))

    @property
    def inactive_moves(self):
        return self.moves-self.active_moves

    @property
    def group_policy(self):
        return self._group_policy

    @group_policy.setter
    def group_policy(self, value):
        assert value in ['synchronize', 'one_of'], 'Should be str: synchronize or one_of'
        self._group_policy = value

    @strictly_typed
    def add_move(self, move: PGMove, auto_active: bool = True) -> None:
        if auto_active:
            if self.group_policy == 'synchronize':
                move.active = True
            if self.group_policy == 'one_of':
                move.active = not bool(self._moves)
        self._moves.add(move)


class PGMove:

    def __init__(self, link_1, link_2):
        self.links = (link_1, link_2)
        self.active = True

    @property
    def links(self):
        return self._links

    @links.setter
    @strictly_typed
    def links(self, links_tuple: tuple[PGLink, PGLink]) -> None:
        self._links = links_tuple

    @property
    def active(self):
        return self._active

    @active.setter
    @strictly_typed
    def active(self, value: bool) -> None:
        self._active = value


class PGLink:

    def __init__(self, end_1, end_2):
        self.ends = (end_1, end_2)

    @property
    def ends(self):
        return self._ends

    @ends.setter
    @strictly_typed
    def ends(self, ends_tuple: tuple[PolarGraph, PolarGraph]) -> None:
        self._ends = ends_tuple


class PolarGraph:

    def __init__(self):
        self.content = PGContent()
        self._links_positive_up = set()
        self._links_negative_down = set()
        self.moves_group = PGMovesGroup()

    @property
    def links_positive_up(self) -> set:
        return copy(self._links_positive_up)

    @property
    def links_negative_down(self) -> set:
        return copy(self._links_negative_down)

    @strictly_typed
    def connect_external_to_its_end(self, pg: PolarGraph,
                                    end: OneOfString(['negative_down', 'positive_up', 'nd', 'pu']) = 'nd') -> None:
        link = PGLink(pg, self)
        if end in ['negative_down', 'nd']:
            opposite_end = 'pu'
            self._links_positive_up.add(link)
            pg._links_negative_down.add(link)
        else:
            opposite_end = 'nd'
            self._links_negative_down.add(link)
            pg._links_positive_up.add(link)
        self.auto_add_moves(link, end)
        pg.auto_add_moves(link, opposite_end)

    @strictly_typed
    def auto_add_moves(self, link: PGLink,
                       end: OneOfString(['negative_down', 'positive_up', 'nd', 'pu']) = 'nd') -> None:
        if end in ['negative_down', 'nd']:
            opposite_links = self._links_negative_down
        else:
            opposite_links = self._links_positive_up
        for i, opposite_link in enumerate(opposite_links):
            new_move = PGMove(link, opposite_link)
            self.moves_group.add_move(new_move)


