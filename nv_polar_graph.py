from __future__ import annotations
from copy import copy
from collections import namedtuple

from nv_typing import *


class PGContentDescriptor:

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        assert len(instance.node_content) > 0, 'Empty content for instance {}'.format(instance)
        if len(instance.node_content) == 1:
            return instance.node_content['whole']
        return instance.node_content

    def __set__(self, instance, value):
        if not hasattr(instance, 'node_content'):
            instance.node_content = {}
        if type(value) != dict:
            instance.node_content['whole'] = value
        else:
            keys = value.keys()
            for key in keys:
                instance.node_content[key] = value[key]


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
    @strictly_typed
    def group_policy(self, value: OneOfString(['synchronize', 'one_of'])) -> None:
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
    def ends(self, ends_tuple: tuple[PolarNode, PolarNode]) -> None:
        self._ends = ends_tuple


class PolarNode:
    content = PGContentDescriptor()

    def __init__(self):
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
    def connect_external_to_its_end(self, pn: PolarNode,
                                    end: OneOfString(['negative_down', 'positive_up', 'nd', 'pu']) = 'nd') -> None:
        link = PGLink(pn, self)
        if end in ['negative_down', 'nd']:
            opposite_end = 'pu'
            self._links_positive_up.add(link)
            pn._links_negative_down.add(link)
        else:
            opposite_end = 'nd'
            self._links_negative_down.add(link)
            pn._links_positive_up.add(link)
        self.auto_add_moves(link, end)
        pn.auto_add_moves(link, opposite_end)

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

    @strictly_typed
    def switch_branch(self, pn: PolarNode, pn_2: PolarNode = None) -> None:
        if self.moves_group.group_policy != 'one_of':
            return
        move_found = False
        for move in self.moves_group.moves:
            first_link_found, second_link_found = False, False
            for link in move.links:
                if pn in link.ends:
                    first_link_found = link
                if pn_2 in link.ends:
                    second_link_found = link
            if (first_link_found and (pn_2 is None)) or (first_link_found and second_link_found):
                move_found = move
                break
        assert move_found, 'Move to PolarNode {} not found'.format(pn)
        for move in self.moves_group.moves:
            if move != move_found:
                move.active = False
            else:
                move.active = True


AttributeTuple = namedtuple('AttributeTuple', ['node_type', 'node_name', 'node_value'])


class AttributeNode(PolarNode):

    @strictly_typed
    def __init__(self, node_type: OneOfString(['title', 'splitter', 'value']), node_name: str = '',
                 node_value: Any = None) -> None:
        super().__init__()
        self.content = AttributeTuple(node_type=node_type, node_name=node_name, node_value=node_value)
        if node_type == 'splitter':
            self.moves_group.group_policy = 'one_of'

    @property
    def value(self):
        return self.content.node_value

    @value.setter
    def value(self, val):
        self.content.node_value = val


class AttributeGraph:

    def __init__(self):
        self._nodes = []

    @strictly_typed
    def add_node(self, an: AttributeNode, to_splitter: AttributeNode = None) -> None:
        self._nodes.append(an)
        if len(self._nodes) == 1:
            return
        if to_splitter:
            assert to_splitter in self._nodes, 'Splitter not found in nodes'
            an.connect_external_to_its_end(to_splitter)
        else:
            an.connect_external_to_its_end(self._nodes[-1])

    @strictly_typed
    def add_title(self, title_name: str) -> None:
        an = AttributeNode('title', title_name)
        self.add_node(an)

    @strictly_typed
    def last_splitter(self) -> Optional[AttributeNode]:
        for node in reversed(self._nodes):
            if node.content.node_type == 'splitter':
                return node

    @strictly_typed
    def add_splitter(self, splitter_name: str, to_splitter: AttributeNode = None) -> None:
        an = AttributeNode('splitter', splitter_name)
        self.add_node(an, to_splitter)

    @strictly_typed
    def add_value(self, value_name: str, to_splitter: AttributeNode = None) -> None:
        an = AttributeNode('value', value_name)
        self.add_node(an, to_splitter)

    @strictly_typed
    def set_value(self, value_name: str, value: Any) -> None:
        node_found = False
        for node in self._nodes:
            if (node.content.node_type == 'value') and (node.content.node_name == value_name):
                node.content.node_value = value
                return
        assert node_found, 'Node for setting value is not found'

    @strictly_typed
    def switch_splitter(self, splitter_name: str, to_value: str) -> None:
        pass

    @strictly_typed
    def get_linear_list(self) -> list[AttributeTuple]:
        pass


if __name__ == '__main__':

    test = 'test_1'
    if test == 'test_1':
        pg_1 = PolarNode()
        pg_2 = PolarNode()
        pg_3 = PolarNode()
        pg_4 = PolarNode()
        pg_5 = PolarNode()
        pg_1.moves_group.group_policy = 'one_of'
        pg_1.connect_external_to_its_end(pg_2, end='nd')
        pg_1.connect_external_to_its_end(pg_4)
        pg_3.connect_external_to_its_end(pg_1)
        pg_5.connect_external_to_its_end(pg_1)

        print('pg_1 = ', pg_1)
        print('pg_2 = ', pg_2)
        print('pg_1 negative = ', pg_1.links_negative_down)
        print('pg_1 positive = ', pg_1.links_positive_up)
        print('pg_2 negative = ', pg_2.links_negative_down)
        print('pg_2 positive = ', pg_2.links_positive_up)

        for lnk in pg_1.links_negative_down:
            print('link', lnk.ends)

        # pg_1.content = {'def': 99}
        pg_1.content = 15
        pg_2.content = pg_3
        print('pg_1.content = ', pg_1.content)
        print('pg_2.content = ', pg_2.content)

        # print('pg_1.content.is_complex = ', pg_1.content.is_complex())
        # print('pg_2.content.is_complex = ', pg_2.content.is_complex())

        print('moves pg_1 = ', pg_1.moves_group.moves)
        print('moves pg_2 = ', pg_2.moves_group.moves)
        print('moves pg_3 = ', pg_3.moves_group.moves)

        for i, pg in enumerate([pg_1, pg_2, pg_3, pg_4, pg_5]):
            print('pg_'+str(i+1), pg)

        pg_1.switch_branch(pg_2, pg_3)

        for mve in pg_1.moves_group.moves:
            print('pg_1 moves = ', mve.active)
            if mve.active:
                lnks = mve.links
                for lnk in lnks:
                    print('active nodes', lnk.ends)

    if test == 'test_2':
        pass

