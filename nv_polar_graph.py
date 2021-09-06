from __future__ import annotations
from copy import copy
# from collections import namedtuple
from collections.abc import Iterable

from nv_typing import *
from nv_names_control import names_control


# class NotActiveHalfMoveError(Exception):
#     pass
# raise NotActiveHalfMoveError('NO ACTIVE ')


class PGContentDescriptor:

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        assert len(instance.element_content) > 0, 'Empty content for instance {}'.format(instance)
        if len(instance.element_content) == 1:
            return instance.element_content['whole']
        return instance.element_content

    def __set__(self, instance, value):
        if not hasattr(instance, 'element_content'):
            instance.element_content = {}
        if type(value) != dict:
            instance.element_content['whole'] = value
        else:
            keys = value.keys()
            for key in keys:
                instance.element_content[key] = value[key]


class PGMovesGroup:

    def __init__(self):
        self._moves = set()

    @property
    @strictly_typed
    def moves(self) -> set[PGMove]:
        return copy(self._moves)

    @property
    @strictly_typed
    def active_move(self) -> Optional[PGMove]:
        active_moves = set(filter(lambda item: item.active, self._moves))
        assert len(active_moves) <= 1, 'Only <= 1 Move should be'
        if active_moves:
            return active_moves.pop()

    @property
    @strictly_typed
    def inactive_moves(self) -> set[PGMove]:
        return copy(self.moves-self.active_moves)

    @strictly_typed
    def add_move(self, move: PGMove) -> None:
        move.active = False  # not bool(self._moves)
        self._moves.add(move)

    def deactivate_all_moves(self):
        for move in self.moves:
            move.active = False

    def random_move_activate(self):
        self.deactivate_all_moves()
        move_random = self.moves.pop()
        move_random.active = True

    @strictly_typed
    def move_activate(self, move: PGMove) -> None:
        assert move in self.moves, 'Move not found in MoveGroup'
        self.deactivate_all_moves()
        move.active = True

    def clear(self):
        self._moves.clear()


class PGMove:

    @strictly_typed
    def __init__(self, link_positive_up: PGLink, link_negative_down: PGLink) -> None:
        self.links = (link_positive_up, link_negative_down)
        self.active = False

    def __repr__(self):
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.node,
                                       self.links[0].opposite_end(self.node), self.links[1].opposite_end(self.node))

    @property
    @strictly_typed
    def links(self) -> tuple[PGLink, PGLink]:
        return self._links

    @links.setter
    @strictly_typed
    def links(self, links_tuple: tuple[PGLink, PGLink]) -> None:
        self._links = links_tuple

    @property
    @strictly_typed
    def node(self) -> PolarNode:
        nodes = [node for node in self._links[0].ends if node in self._links[1].ends]
        assert nodes, 'Node not found for move'
        assert len(nodes) <= 1, 'Only 1 node should be'
        return nodes[0]

    @property
    def active(self):
        return self._active

    @active.setter
    @strictly_typed
    def active(self, value: bool) -> None:
        self._active = value


class PGLink:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self, end_1: PolarNode, end_2: PolarNode) -> None:
        self.ends = (end_1, end_2)
        self._graph = end_1.graph
        self.graph.add_link(self)

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.ends[0], self.ends[1])  # {}, self.graph,

    @property
    @strictly_typed
    def graph(self) -> PolarGraph:
        return self._graph

    @property
    @strictly_typed
    def ends(self) -> tuple[PolarNode, PolarNode]:
        return self._ends

    @ends.setter
    @strictly_typed
    def ends(self, ends_tuple: tuple[PolarNode, PolarNode]) -> None:
        self._ends = ends_tuple

    @strictly_typed
    def opposite_end(self, current_end: PolarNode) -> PolarNode:
        assert current_end in self._ends, 'Current end not found'
        return (set(self._ends) - {current_end}).pop()


@names_control
class PolarGraph:

    def __init__(self):
        self._nodes = []
        self._links = []
        self._infinity_node_positive_up = PolarNode(self, True)
        self._infinity_node_negative_down = PolarNode(self, True)
        self._infinity_node_positive_up.connect_to_its_end(self._infinity_node_negative_down)

    @property
    def infinity_node_positive_up(self):
        return self._infinity_node_positive_up

    @property
    def infinity_node_negative_down(self):
        return self._infinity_node_negative_down

    @strictly_typed
    def add_node(self, pn: PolarNode) -> None:
        self._nodes.append(pn)

    @strictly_typed
    def add_link(self, link: PGLink) -> None:
        self._links.append(link)

    @strictly_typed
    def get_link(self, pn_1: PolarNode, pn_2: PolarNode) -> PGLink:
        links = [link for link in self._links if ((pn_1 in link.ends) and (pn_2 in link.ends))]
        assert links, 'Link not found'
        assert len(links) <= 1, 'Only 1 link should be with the same PolarNodes tuple'
        return links[0]


@names_control
class PolarNode:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self, graph: PolarGraph, infinity_node_init: bool = False) -> None:
        self._graph = graph
        self.graph.add_node(self)
        self._links_positive_up = set()
        self._links_negative_down = set()
        self.moves_group = PGMovesGroup()
        if not infinity_node_init:
            self.connect_to_its_end(self.graph.infinity_node_positive_up)
            self.graph.infinity_node_negative_down.connect_to_its_end(self)

    @property
    @strictly_typed
    def graph(self) -> PolarGraph:
        return self._graph

    @property
    @strictly_typed
    def links_positive_up(self) -> set[PGLink]:
        return copy(self._links_positive_up)

    @property
    @strictly_typed
    def links_negative_down(self) -> set[PGLink]:
        return copy(self._links_negative_down)

    @strictly_typed
    def get_move(self, pn_1: PolarNode, pn_2: PolarNode) -> PGMove:
        moves = [move for move in self.moves_group.moves
                 if (self.graph.get_link(self, pn_1) in move.links)
                 and (self.graph.get_link(self, pn_2) in move.links)]
        assert moves, 'Move not found'
        assert len(moves) <= 1, 'Only 1 Move should be with the same PolarNodes tuple'
        return moves[0]

    @strictly_typed
    def connect_to_its_end(self, pn: PolarNode,
                           end: OneOfString(['negative_down', 'positive_up', 'nd', 'pu']) = 'nd') -> None:
        assert pn.graph == self.graph, 'Different graphs of nodes for connections'
        link = PGLink(pn, self)
        if end in ['negative_down', 'nd']:
            opposite_end = 'pu'
            down_node, up_node = self, pn
        else:
            opposite_end = 'nd'
            down_node, up_node = pn, self
        if down_node.graph.infinity_node_positive_up in \
                [link.opposite_end(down_node) for link in down_node._links_positive_up]:
            down_node.graph.infinity_node_positive_up._links_negative_down.remove(down_node._links_positive_up.pop())
            down_node._links_positive_up.clear()
            down_node.moves_group.clear()
        down_node._links_positive_up.add(link)
        if up_node.graph.infinity_node_negative_down in \
                [link.opposite_end(up_node) for link in up_node._links_negative_down]:
            up_node.graph.infinity_node_negative_down._links_positive_up.remove(up_node._links_negative_down.pop())
            up_node._links_negative_down.clear()
            up_node.moves_group.clear()
        up_node._links_negative_down.add(link)
        self.auto_add_moves(link, end)
        pn.auto_add_moves(link, opposite_end)

    @strictly_typed
    def auto_add_moves(self, link: PGLink,
                       end: OneOfString(['negative_down', 'positive_up', 'nd', 'pu']) = 'nd') -> None:
        if end in ['negative_down', 'nd']:
            opposite_links = self._links_negative_down
        else:
            opposite_links = self._links_positive_up
        for opposite_link in opposite_links:
            new_move = PGMove(link, opposite_link) if end in ['negative_down', 'nd'] else PGMove(opposite_link, link)
            self.moves_group.add_move(new_move)
            self.moves_group.random_move_activate()

    @strictly_typed
    def switch_branch(self, pn: PolarNode, pn_2: PolarNode = None) -> None:
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

    @strictly_typed
    def next_active_move_node(self, direction: OneOfString(['negative_down', 'positive_up', 'nd', 'pu']) = 'nd')\
            -> PolarNode:
        move_end = int(direction in ['negative_down', 'nd'])
        active_move = self.moves_group.active_move
        active_link = active_move.links[move_end]
        return active_link.opposite_end(self)

    @strictly_typed
    def next_nodes(self, direction: OneOfString(['negative_down', 'positive_up', 'nd', 'pu']) = 'nd')\
            -> list[PolarNode]:
        move_end = int(direction in ['negative_down', 'nd'])
        if move_end:
            next_links = self._links_negative_down
        else:
            next_links = self._links_positive_up
        return [link.opposite_end(self) for link in next_links]


class AttributeTuple:
    def __init__(self, node_type, node_name, node_value):
        self.node_type = node_type
        self.node_name = node_name
        self.node_value = node_value


class AttributeNode(PolarNode):

    @strictly_typed
    def __init__(self, node_type: OneOfString(['title', 'splitter', 'value']), node_name: str = '',
                 node_value: Any = None) -> None:
        super().__init__()
        self.content = AttributeTuple(node_type, node_name, node_value)

    @property
    def value(self):
        return self.content.node_value

    @value.setter
    def value(self, val):
        self.content.node_value = val


class AttributeGraph(PolarGraph):

    def __init__(self):
        super().__init__()
        self._splitters_last_nodes = []  # list[an]
        self._associations = {}  # {(split_an, str_val): derived_an}

    @strictly_typed
    def associate(self, splitter_an: AttributeNode, splitter_str_value: str, derived_an: AttributeNode) -> None:
        assert splitter_an in self._nodes, 'Splitter not found in nodes list'
        assert splitter_an.content.node_type == 'splitter', 'Can be only splitter associated'
        assert splitter_str_value in splitter_an.content.node_value, 'Splitter str-value not found in values list'
        self._associations[(splitter_an, splitter_str_value)] = derived_an

    @strictly_typed
    def add_node(self, an: AttributeNode, to_splitter: AttributeNode = None, associated_splitter_value: str = '',
                 out_splitter: bool = False) -> None:
        self._nodes.append(an)
        if len(self._nodes) == 1:
            return
        last_node = self._nodes[-1]
        if to_splitter:
            assert to_splitter in self._nodes, 'Splitter not found in nodes'
            if last_node != to_splitter:
                self._splitters_last_nodes.append(last_node)
            an.connect_to_its_end(to_splitter)
            self.associate(to_splitter, associated_splitter_value, an)
        elif out_splitter:
            for splitters_last_node in self._splitters_last_nodes:
                an.connect_to_its_end(splitters_last_node)
            self._splitters_last_nodes.clear()
        else:
            an.connect_to_its_end(last_node)

    @strictly_typed
    def add_typed_node(self, node_type: OneOfString(['title', 'splitter', 'value']), node_name: str,
                       to_splitter: AttributeNode = None, associated_splitter_value: str = '') -> None:
        an = AttributeNode(node_type, node_name)
        self.add_node(an, to_splitter, associated_splitter_value)

    @strictly_typed
    def set_node_value(self, value_name: str, value: Any) -> None:
        node_found = False
        for node in self._nodes:
            if (node.content.node_type in ['value', 'splitter']) and (node.content.node_name == value_name):
                if node.content.node_type == 'splitter':
                    assert isinstance(value, Iterable), 'Need iterable value for splitter'
                    for val in value:
                        assert type(val) == str, 'Values in splitter should be str'
                node.content.node_value = value
                return
        assert node_found, 'Node for setting value is not found'

    @strictly_typed
    def last_splitter(self) -> Optional[AttributeNode]:
        for node in reversed(self._nodes):
            if node.content.node_type == 'splitter':
                return node

    @strictly_typed
    def switch_splitter(self, splitter_name: str, to_splitter_str_value: str) -> None:
        node_found = False
        for node in self._nodes:
            if (node.content.node_type == 'splitter') and (node.content.node_name == splitter_name):
                node_found = True
                node.switch_branch(self._associations[(node, to_splitter_str_value)])
        assert node_found, 'Node for setting value is not found'

    @strictly_typed
    def get_linear_list(self) -> list[AttributeTuple]:
        pass


if __name__ == '__main__':

    test = 'test_1'
    if test == 'test_1':
        pg = PolarGraph()
        print('pu infinity', pg.infinity_node_positive_up)
        print('nd infinity', pg.infinity_node_negative_down)
        # print('Infinity node', pg._infinity_node_positive_up) #
        pg_1 = PolarNode(pg, name='PolarNode_pg_1')
        # print('take by name', PolarNode.get_inst_by_name('PolarNode_test_2'))
        print('pg_1 name = ', pg_1.name)
        pg_2 = PolarNode(pg, name='PolarNode_pg_2')
        pg_3 = PolarNode(pg, name='PolarNode_pg_3')
        pg_4 = PolarNode(pg, name='PolarNode_pg_4')
        pg_5 = PolarNode(pg, name='PolarNode_pg_5')
        print('pg1 links neg down =', pg_1.links_negative_down)
        pg_1.moves_group.group_policy = 'one_of'
        pg_1.connect_to_its_end(pg_2, end='nd')
        pg_1.connect_to_its_end(pg_4)
        pg_3.connect_to_its_end(pg_1)
        pg_5.connect_to_its_end(pg_1)

        print('get link = ', pg.get_link(pg_1, pg_5))

        print('get move = ', pg_1.get_move(pg_2, pg_5))

        print('pg_1 = ', pg_1)
        print('pg_2 = ', pg_2)
        print('pg_1 negative = ', pg_1.links_negative_down)
        my_lnk = pg_1.links_negative_down.pop()
        my_lnk.content = 13
        print('link content = ', my_lnk.content)
        print('pg_1 positive = ', pg_1.links_positive_up)
        print('pg_2 negative = ', pg_2.links_negative_down)
        print('pg_2 positive = ', pg_2.links_positive_up)

        curr_node = pg_1
        for lnk in curr_node.links_negative_down:
            print('link', lnk.opposite_end(curr_node))

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

        for i, pg_i in enumerate([pg_1, pg_2, pg_3, pg_4, pg_5]):
            print('pg_'+str(i+1), pg_i)

        pg_1.switch_branch(pg_2, pg_3)
        pg.infinity_node_positive_up.switch_branch(pg_2)
        pg.infinity_node_negative_down.switch_branch(pg_3)

        for mve in pg_1.moves_group.moves:
            print('pg_1 moves = ', mve.active)
            if mve.active:
                lnks = mve.links
                for lnk in lnks:
                    print('active nodes', lnk.opposite_end(pg_1))

        print('next nd for pg_1', pg_1.next_active_move_node())
        print('next pu for pg_1', pg_1.next_active_move_node('pu'))
        print('all nd for pg_1', pg_1.next_nodes())
        print('all pu for pg_1', pg_1.next_nodes('pu'))
        print('next nd for pg_2', pg_2.next_active_move_node())
        print('next nd for pg_3', pg_3.next_active_move_node())
        print('next pu for nd inf', pg.infinity_node_negative_down.next_active_move_node('pu'))
        print('next nd for pu inf', pg.infinity_node_positive_up.next_active_move_node())
        print('next pu for pu inf', pg.infinity_node_positive_up.next_active_move_node('pu'))
        print('next nd for nd inf', pg.infinity_node_negative_down.next_active_move_node())

    if test == 'test_2':
        pass
        # NT = namedtuple('NT', ['q', 'a'])
        # nt = NT(2, 3)
        # nt.a = 4
        # nt.q = 5

