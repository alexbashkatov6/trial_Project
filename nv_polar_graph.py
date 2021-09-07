from __future__ import annotations
from copy import copy
from collections.abc import Iterable
from itertools import product

from nv_typing import *
from nv_names_control import names_control


class End:
    @strictly_typed
    def __init__(self, str_end: str) -> None:
        assert str_end in ['negative_down', 'positive_up', 'nd', 'pu'], \
            "Value should be one of 'negative_down', 'positive_up', 'nd', 'pu'"
        self.str_end = str_end

    def __str__(self):
        return self.str_end

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.str_end)

    @property
    @strictly_typed
    def is_negative_down(self) -> bool:
        return self.str_end in ['negative_down', 'nd']

    @property
    @strictly_typed
    def is_positive_up(self) -> bool:
        return self.str_end in ['positive_up', 'pu']

    @property
    @strictly_typed
    def opposite_end(self) -> End:
        if self.is_negative_down:
            return End('pu')
        else:
            return End('nd')


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
        return copy(self.moves - {self.active_move})

    @strictly_typed
    def add_move(self, move: PGMove) -> None:
        move.active = False
        self._moves.add(move)

    def deactivate_all_moves(self):
        for move in self.moves:
            move.active = False

    def random_move_activate(self):
        self.deactivate_all_moves()
        move_random = self.moves.pop()
        move_random.active = True

    @strictly_typed
    def choice_move_activate(self, move: PGMove) -> None:
        assert move in self.moves, 'Move not found in MoveGroup'
        self.deactivate_all_moves()
        move.active = True

    def clear(self):
        self._moves.clear()


class PGMove:

    @strictly_typed
    def __init__(self, node_place: PolarNode, link_positive_up: PGLink, link_negative_down: PGLink) -> None:
        self.links = (link_positive_up, link_negative_down)
        self.node_place = node_place
        self.active = False
        assert link_positive_up in self.node_place.links_positive_up, 'check positive link'
        assert link_negative_down in self.node_place.links_negative_down, 'check negative link'

    def __repr__(self):
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.node_place,
                                       self.links[0].opposite_end(self.node_place),
                                       self.links[1].opposite_end(self.node_place))

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
    def node_positive_up(self) -> PolarNode:
        return self.links[0].opposite_end(self.node_place)

    @property
    @strictly_typed
    def node_negative_down(self) -> PolarNode:
        return self.links[1].opposite_end(self.node_place)

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
    def __init__(self, end_1: PolarNode, end_2: PolarNode, is_stable: bool = False) -> None:
        self.ends = (end_1, end_2)
        self.stable = is_stable

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.ends[0], self.ends[1])  # {}, self.graph,

    @property
    @strictly_typed
    def stable(self) -> bool:
        return self._stable

    @stable.setter
    @strictly_typed
    def stable(self, is_stable: bool) -> None:
        self._stable = is_stable

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
        self._sub_graphs = {}  # {tag: list[PG]}

        self._infinity_node_positive_up = self._init_node()
        self._infinity_node_negative_down = self._init_node()
        self._connect_nodes(self.inf_node_pu, self.inf_node_nd, link_is_stable=True)
        self._connect_nodes(self.inf_node_pu, self.inf_node_nd, flip=True)

    @property
    def inf_node_pu(self):
        return self._infinity_node_positive_up

    @property
    def inf_node_nd(self):
        return self._infinity_node_negative_down

    @property
    @strictly_typed
    def nodes(self) -> list[PolarNode]:
        return copy(self._nodes)

    @property
    @strictly_typed
    def links(self) -> list[PGLink]:
        return copy(self._links)

    # @strictly_typed
    # def get_sub_graphs(self, tag: str) -> list[PolarGraph]:
    #     return copy(self._sub_graphs[tag])

    @strictly_typed
    def _add_node(self, pn: PolarNode) -> None:
        self._nodes.append(pn)

    @strictly_typed
    def _add_link(self, link: PGLink) -> None:
        self._links.append(link)

    @strictly_typed
    def get_link(self, pn_1: PolarNode, pn_2: PolarNode) -> Optional[PGLink]:
        links = [link for link in self._links if ((pn_1 in link.ends) and (pn_2 in link.ends))]
        if {pn_1, pn_2} == {self.inf_node_pu, self.inf_node_nd}:
            if len(self.links) <= 1:
                return
            return self.links[1]
        else:
            assert len(links) <= 1, 'Only 1 link should be with the same PolarNodes tuple'
        if links:
            return links[0]

    @strictly_typed
    def _init_node(self) -> PolarNode:
        node = PolarNode()
        self._add_node(node)
        return node

    @strictly_typed
    def _connect_nodes(self, pn_1: PolarNode, pn_2: PolarNode,
                       end_pn_1: End = End('pu'), end_pn_2: End = End('nd'),
                       flip: bool = False, link_is_stable: bool = False) -> PGLink:
        # appends pn_1 at down of pn_2 as default
        assert {pn_1, pn_2} <= set(self.nodes), 'Nodes {}, {} not found in graph'.format(pn_1, pn_2)
        assert not self.get_link(pn_1, pn_2), 'Link {}, {} already exists'.format(pn_1, pn_2)
        link = PGLink(pn_1, pn_2, link_is_stable)
        if flip:
            end_pn_1, end_pn_2 = end_pn_2, end_pn_1
        pn_1.add_link_to_node_end(link, end_pn_1)
        pn_2.add_link_to_node_end(link, end_pn_2)
        self._add_link(link)
        return link

    @strictly_typed
    def _disconnect_nodes(self, pn_s: tuple[PolarNode, PolarNode] = None, link: PGLink = None) -> None:
        assert pn_s or link, 'Not valid input data'
        if pn_s:
            pn_1, pn_2 = pn_s
            assert not link, 'Redundant input data: link'
            link = self.get_link(pn_1, pn_2)
        else:
            pn_1, pn_2 = link.ends
        pn_1.remove_link(link)
        pn_2.remove_link(link)
        self._links.remove(link)

    @strictly_typed
    def insert_node(self, positive_up_node: PolarNode = None,
                    negative_down_node: PolarNode = None,
                    insertion_node: PolarNode = None,
                    end_of_positive_up: End = End('nd'), end_of_negative_down: End = End('pu'),
                    make_pu_stable: bool = False, make_nd_stable: bool = False) -> PolarNode:
        # positive_up and negative_down for insertion_node, but their ends is
        if not positive_up_node:
            positive_up_node = self.inf_node_pu
        if not negative_down_node:
            negative_down_node = self.inf_node_nd
        if not insertion_node:
            insertion_node = self._init_node()
        existing_link = self.get_link(positive_up_node, negative_down_node)
        if existing_link and not existing_link.stable:
            self._disconnect_nodes((positive_up_node, negative_down_node))
        self._connect_nodes(insertion_node, positive_up_node, End('pu'), end_of_positive_up,
                            link_is_stable=make_pu_stable)
        self._connect_nodes(insertion_node, negative_down_node, End('nd'), end_of_negative_down,
                            link_is_stable=make_nd_stable)
        return insertion_node

    @strictly_typed
    def cut_subgraph(self, pns: list[PolarNode]) -> PolarGraph:
        return self

    @strictly_typed
    def find_active_route(self, pn_1: PolarNode, pn_2: PolarNode) -> PolarGraph:
        return self

    @strictly_typed
    def find_all_routes(self, pn_1: PolarNode, pn_2: PolarNode) -> list[PolarGraph]:
        return [self]

    @strictly_typed
    def find_coverage(self, pn_1: PolarNode,
                      direction: End = End('nd')) -> PolarGraph:
        return self


@names_control
class PolarNode:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self) -> None:
        self._links_positive_up = set()
        self._links_negative_down = set()
        self.moves_group = PGMovesGroup()

    @property
    @strictly_typed
    def links_positive_up(self) -> set[PGLink]:
        return copy(self._links_positive_up)

    @property
    @strictly_typed
    def links_negative_down(self) -> set[PGLink]:
        return copy(self._links_negative_down)

    @strictly_typed
    def add_link_to_node_end(self, link: PGLink,
                             node_end: End = End('nd')) -> None:
        assert self in link.ends, 'Node not found in link ends'
        if node_end.is_negative_down:
            self._links_negative_down.add(link)
        else:
            self._links_positive_up.add(link)
        self.refresh_moves()

    @strictly_typed
    def remove_link(self, link: PGLink) -> None:
        assert self in link.ends, 'Node not found in link ends'
        if link in self._links_negative_down:
            self._links_negative_down.remove(link)
            self.refresh_moves()
            return
        if link in self._links_positive_up:
            self._links_positive_up.remove(link)
            self.refresh_moves()
            return
        assert False, 'Link not found in node'

    def refresh_moves(self):
        self.moves_group.clear()
        if self._links_positive_up and self._links_negative_down:
            product_tuples = product(self._links_positive_up, self._links_negative_down)
            for product_tuple in product_tuples:
                self.moves_group.add_move(PGMove(self, *product_tuple))
                self.moves_group.random_move_activate()

    @strictly_typed
    def get_move(self, pn_1: PolarNode, pn_2: PolarNode) -> Optional[PGMove]:
        if pn_1 is pn_2:
            return
        moves = [move for move in self.moves_group.moves
                 if {pn_1, pn_2} <= {move.node_positive_up, move.node_negative_down}]
        assert len(moves) <= 1, 'No more then 1 Move should be with the same PolarNodes tuple'
        if moves:
            return moves[0]

    @strictly_typed
    def next_active_move_node(self, direction: End = End('nd')) -> PolarNode:
        active_move = self.moves_group.active_move
        if direction.is_negative_down:
            return active_move.node_negative_down
        else:
            return active_move.node_positive_up

    @strictly_typed
    def next_nodes(self, direction: End = End('nd'))\
            -> list[PolarNode]:
        if direction.is_negative_down:
            next_links = self._links_negative_down
        else:
            next_links = self._links_positive_up
        return [link.opposite_end(self) for link in next_links]

    @strictly_typed
    def switch_branch(self, pn: PolarNode, pn_2: PolarNode = None, save_second_current: bool = False) -> None:
        if pn_2:
            new_active_move = self.get_move(pn, pn_2)
            assert new_active_move, 'Move not found'
            self.moves_group.choice_move_activate(new_active_move)
            return
        elif save_second_current:
            current_active_move = self.moves_group.active_move
            active_nodes = current_active_move.node_positive_up, current_active_move.node_negative_down
            for active_node in active_nodes:
                new_active_move = self.get_move(pn, active_node)
                if new_active_move:
                    self.moves_group.choice_move_activate(new_active_move)
                    return
            assert False, 'Move not found'
        else:
            move_candidates = []
            for link in (self.links_positive_up.union(self.links_negative_down)):
                opposite_node = link.opposite_end(self)
                new_active_move = self.get_move(pn, opposite_node)
                if new_active_move:
                    move_candidates.append(new_active_move)
            assert move_candidates, 'Move not found'
            assert len(move_candidates) <= 1, 'More then 1 variant for active move'
            self.moves_group.choice_move_activate(move_candidates[0])


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
    def _add_node(self, an: AttributeNode, to_splitter: AttributeNode = None, associated_splitter_value: str = '',
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
        self._add_node(an, to_splitter, associated_splitter_value)

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

    test = 'test_2'
    if test == 'test_1':

        def check_inf_moves(text):
            print(text)
            for mv in pg.inf_node_pu.moves_group.moves:
                print('mv +inf pos/neg = ', mv.node_positive_up, mv.node_negative_down)
            for mv in pg.inf_node_nd.moves_group.moves:
                print('mv -inf pos/neg = ', mv.node_positive_up, mv.node_negative_down)
            print('end of '+text)

        pg = PolarGraph()
        print('pu infinity', pg.inf_node_pu)
        print('nd infinity', pg.inf_node_nd)
        # check_inf_moves('before all connections: ')
        # print('Infinity node', pg._infinity_node_positive_up) #
        pg_1 = PolarNode(pg, name='PolarNode_pg_1')
        # check_inf_moves('after pg_1 creation: ')
        # print('take by name', PolarNode.get_inst_by_name('PolarNode_test_2'))
        print('pg_1 name = ', pg_1.name)
        pg_2 = PolarNode(pg, name='PolarNode_pg_2')
        pg_3 = PolarNode(pg, name='PolarNode_pg_3')
        pg_4 = PolarNode(pg, name='PolarNode_pg_4')
        pg_5 = PolarNode(pg, name='PolarNode_pg_5')
        # check_inf_moves('after pg_1-5 creation: ')
        print('pg1 links neg down =', pg_1.links_negative_down)
        pg_1.connect_to_its_end(pg_2, its_end=End('nd'), remove_infinity=False)
        # check_inf_moves('after connect pg_1 pg_2: ')
        pg_1.connect_to_its_end(pg_4, remove_infinity=False)
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

        pg_1.switch_branch(pg_4, pg_3)

        pg.inf_node_pu.switch_branch(pg_2)
        pg.inf_node_nd.switch_branch(pg_3)

        print('active nodes: ', pg_1.moves_group.active_move.node_positive_up,
              pg_1.moves_group.active_move.node_negative_down)

        print('next nd for pg_1', pg_1.next_active_move_node())
        print('next pu for pg_1', pg_1.next_active_move_node(End('pu')))
        print('all nd for pg_1', pg_1.next_nodes())
        print('all pu for pg_1', pg_1.next_nodes(End('pu')))
        print('next nd for pg_2', pg_2.next_active_move_node())
        print('next nd for pg_3', pg_3.next_active_move_node())
        print('next pu for nd inf', pg.inf_node_nd.next_active_move_node(End('pu')))
        print('next nd for pu inf', pg.inf_node_pu.next_active_move_node())
        print('next pu for pu inf', pg.inf_node_pu.next_active_move_node(End('pu')))
        print('next nd for nd inf', pg.inf_node_nd.next_active_move_node())
        print('all nd for pu inf', pg.inf_node_pu.next_nodes())

    if test == 'test_2':

        pg = PolarGraph()
        print('pg.inf_node_pu ', pg.inf_node_pu)
        print('pg.inf_node_nd ', pg.inf_node_nd)
        pn_01 = pg.insert_node()  # make_nd_stable=True
        pn_02 = pg.insert_node(negative_down_node=pn_01)
        pn_03 = pg.insert_node(negative_down_node=pn_01)
        pn_04 = pg.insert_node(positive_up_node=pn_01)
        pn_05 = pg.insert_node(positive_up_node=pn_01)
        print('pn_01 ', pn_01)
        print('pg nodes ', pg.nodes)
        for node_ in pg.nodes:
            print('active move before = ', node_.moves_group.active_move)
        pn_01.switch_branch(pn_04, save_second_current=True)
        for node_ in pg.nodes:
            print('active move after = ', node_.moves_group.active_move)
        print('pg links len ', len(pg.links))
        print('pg links ', pg.links)
        print('pn_01 next all nd ', pn_01.next_nodes())
        print('pn_01 next all pu ', pn_01.next_nodes(End('pu')))
        print('pn_01 next active nd ', pn_01.next_active_move_node())
        print('pn_01 next active pu ', pn_01.next_active_move_node(End('pu')))

        # end_ = End('nd')
        # print(end_.is_positive_up)
        # print({1,2,3,4} <= set([1,2,3,4]))
        pass
        # NT = namedtuple('NT', ['q', 'a'])
        # nt = NT(2, 3)
        # nt.a = 4
        # nt.q = 5
