from __future__ import annotations
from copy import copy, deepcopy
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

    @strictly_typed
    def __eq__(self, other: Union[str, End]) -> bool:
        if type(other) == str:
            other = End(other)
        return (self.is_positive_up and other.is_positive_up) or (self.is_negative_down and other.is_negative_down)

    def __hash__(self):
        return hash(self.str_end)

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


class EndOfPolarNode:

    @strictly_typed
    def __init__(self, pn: PolarNode, end: End = End('nd')) -> None:
        self._pn = pn
        self._end = end

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.pn, self.end)

    @property
    @strictly_typed
    def pn(self) -> PolarNode:
        return self._pn

    @property
    @strictly_typed
    def end(self) -> End:
        return self._end

    @property
    @strictly_typed
    def other_pn_end(self) -> EndOfPolarNode:
        return EndOfPolarNode(self.pn, self.end.opposite_end)

    @strictly_typed
    def __eq__(self, other: EndOfPolarNode) -> bool:
        return (self.end == other.end) and (self.pn is other.pn)

    def __hash__(self):
        return hash((self.pn, self.end))


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
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self, node_place: PolarNode, link_positive_up: PGLink, link_negative_down: PGLink) -> None:
        self.links = (link_positive_up, link_negative_down)
        self.node_place = node_place
        self.active = False
        assert link_positive_up in self.node_place.links_positive_up, 'check positive link'
        assert link_negative_down in self.node_place.links_negative_down, 'check negative link'

    def __repr__(self):
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.node_place,
                                       self.links[0].opposite_pn(self.node_place),
                                       self.links[1].opposite_pn(self.node_place))

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
        return self.links[0].opposite_pn(self.node_place)

    @property
    @strictly_typed
    def node_negative_down(self) -> PolarNode:
        return self.links[1].opposite_pn(self.node_place)

    @property
    def active(self):
        return self._active

    @active.setter
    @strictly_typed
    def active(self, value: bool) -> None:
        self._active = value


class PGLinkGroup:

    @strictly_typed
    def __init__(self, end_pn_1: EndOfPolarNode, end_pn_2: EndOfPolarNode, first_link_is_stable: bool = False) -> None:
        assert end_pn_1 != end_pn_2, 'Cannot connect pn to itself'
        self.end_pns = (end_pn_1, end_pn_2)
        self._links = set()
        self.init_link(first_link_is_stable)

    @property
    @strictly_typed
    def links(self) -> set[PGLink]:
        return copy(self._links)

    @property
    @strictly_typed
    def stable_link(self) -> Optional[PGLink]:
        stable_links = set(filter(lambda x: x.stable, self._links))
        assert len(stable_links) <= 1, '2 stable links was found'
        if stable_links:
            return stable_links.pop()

    @property
    @strictly_typed
    def unstable_links(self) -> set[PGLink]:
        stable_link = self.stable_link
        if stable_link:
            return self.links-{stable_link}
        else:
            return self.links

    @strictly_typed
    def get_link(self, stable: bool = False) -> Optional[PGLink]:
        # gets link by stability
        if stable:
            return self.stable_link
        else:
            unstable_links = self.unstable_links
            if unstable_links:
                return unstable_links.pop()

    @property
    @strictly_typed
    def count_of_links(self) -> int:
        return len(self._links)

    @property
    @strictly_typed
    def end_pns(self) -> tuple[EndOfPolarNode, EndOfPolarNode]:
        return self._end_pns

    @end_pns.setter
    @strictly_typed
    def end_pns(self, end_pns_tuple: tuple[EndOfPolarNode, EndOfPolarNode]) -> None:
        self._end_pns = end_pns_tuple

    @property
    @strictly_typed
    def pns(self) -> tuple[PolarNode, PolarNode]:
        return self.end_pns[0].pn, self.end_pns[1].pn

    @strictly_typed
    def end_of_pn(self, pn: PolarNode) -> End:
        assert pn in self.pns, 'Polar node not found'
        for end_pn in self.end_pns:
            if end_pn.pn is pn:
                return end_pn.end

    @strictly_typed
    def init_link(self, init_stable: bool = False) -> PGLink:
        assert not(self.stable_link and init_stable), 'Only 1 stable link may be between same nodes'
        new_link = PGLink(self, init_stable)
        self._links.add(new_link)
        return new_link

    @strictly_typed
    def remove_link(self, link: PGLink) -> None:
        self._links.remove(link)


class PGLink:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self, links_group: PGLinkGroup, is_stable: bool = False) -> None:
        self.stable = is_stable
        self._group = links_group

    def __repr__(self):
        stable_str = 'stable' if self.stable else ''
        return '{}({}-{}, {}-{}, {})'.format(self.__class__.__name__,
                                             self.end_pns[0].pn, self.end_pns[0].end,
                                             self.end_pns[1].pn, self.end_pns[1].end, stable_str)

    @property
    @strictly_typed
    def group(self) -> PGLinkGroup:
        return self._group

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
    def end_pns(self) -> tuple[EndOfPolarNode, EndOfPolarNode]:
        return self.group.end_pns

    @property
    @strictly_typed
    def pns(self) -> tuple[PolarNode, PolarNode]:
        return self.group.pns

    @strictly_typed
    def opposite_pn(self, current_pn: PolarNode) -> PolarNode:
        assert current_pn in self.pns, 'Current end not found'
        return (set(self.pns) - {current_pn}).pop()


class PGMovesState:

    @strictly_typed
    def __init__(self, pg: PolarGraph) -> None:
        self._moves = []
        for pn in pg.nodes:
            self._moves.append(pn.moves_group.active_move)

    @strictly_typed
    def reset_state(self) -> None:
        for move in self._moves:
            move.node_place.switch_branch(move)


@names_control
class PolarGraph:

    def __init__(self):
        self._nodes = []
        self._link_groups = []
        self._links = []
        # self._sub_graphs = {}  # {tag: list[PG]}

        self._infinity_node_positive_up = self._init_node()
        self._infinity_node_negative_down = self._init_node()
        self.connect_nodes(self.inf_node_pu.end_pu, self.inf_node_nd.end_nd, link_is_stable=True)
        self.connect_nodes(self.inf_node_pu.end_nd, self.inf_node_nd.end_pu)

    # @strictly_typed
    # def get_sub_graphs(self, tag: str) -> list[PolarGraph]:
    #     return copy(self._sub_graphs[tag])

    @strictly_typed
    def _init_node(self) -> PolarNode:
        node = PolarNode()
        self._add_node(node)
        return node

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
    def link_groups(self) -> list[PGLinkGroup]:
        return copy(self._link_groups)

    def refresh_link_groups_and_links(self):
        self._links.clear()
        for link_group in self.link_groups:
            if link_group.count_of_links == 0:
                self._link_groups.remove(link_group)
            else:
                self._links.extend(link_group.links)

    @property
    @strictly_typed
    def links(self) -> list[PGLink]:
        return copy(self._links)

    @strictly_typed
    def _add_node(self, pn: PolarNode) -> None:
        self._nodes.append(pn)

    @strictly_typed
    def _add_link_group(self, link_group: PGLinkGroup) -> None:
        self._link_groups.append(link_group)

    @strictly_typed
    def _get_link_group(self, end_pn_1: EndOfPolarNode, end_pn_2: EndOfPolarNode) -> Optional[PGLinkGroup]:
        link_groups = [link_group for link_group in self.link_groups
                       if {end_pn_1, end_pn_2} == set(link_group.end_pns)]
        assert len(link_groups) <= 1, '2 link_groups with equal nodes and ends was found'
        if link_groups:
            return link_groups[0]

    @strictly_typed
    def _count_link_groups_eq_nodes(self, pn_1: PolarNode, pn_2: PolarNode) -> int:
        ends_combinations = product([End('nd'), End('pu')], [End('nd'), End('pu')])
        count = 0
        for ends_combination in ends_combinations:
            end_candidate_pn_1, end_candidate_pn_2 = \
                EndOfPolarNode(pn_1, ends_combination[0]), EndOfPolarNode(pn_2, ends_combination[1])
            count += int(bool(self._get_link_group(end_candidate_pn_1, end_candidate_pn_2)))
        return count

    @strictly_typed
    def _check_new_link_group_existing_possibility(self, end_pn_1: EndOfPolarNode, end_pn_2: EndOfPolarNode) -> bool:
        return not bool(self._get_link_group(end_pn_1, end_pn_2))

    @strictly_typed
    def _check_new_link_group_count_possibility(self, pn_1: PolarNode, pn_2: PolarNode) -> bool:
        count_existing = self._count_link_groups_eq_nodes(pn_1, pn_2)
        return bool(1 - count_existing + int(bool({pn_1, pn_2} & {self.inf_node_nd, self.inf_node_pu})))

    @strictly_typed
    def _init_new_link_group(self, end_pn_1: EndOfPolarNode, end_pn_2: EndOfPolarNode,
                             first_link_is_stable: bool = False) -> PGLinkGroup:
        assert self._check_new_link_group_existing_possibility(end_pn_1, end_pn_2), 'Lg already exists'
        assert self._check_new_link_group_count_possibility(end_pn_1.pn, end_pn_2.pn), \
            'Exceeds count of max LinkGroup between same nodes'
        new_lg = PGLinkGroup(end_pn_1, end_pn_2, first_link_is_stable)
        self._link_groups.append(new_lg)
        return new_lg

    @strictly_typed
    def get_link_from_group(self, plg: PGLinkGroup, arbitrary_stable: bool = False, stable: bool = False) \
            -> Optional[PGLink]:
        if arbitrary_stable:
            return plg.links.pop()
        else:
            return plg.get_link(stable)

    @strictly_typed
    def connect_nodes(self, end_pn_1: EndOfPolarNode, end_pn_2: EndOfPolarNode,
                      link_is_stable: bool = False) -> PGLink:
        assert not (end_pn_1.pn is end_pn_2.pn), 'Cannot connect node {} to himself'.format(end_pn_1.pn)
        assert {end_pn_1.pn, end_pn_2.pn} <= set(self.nodes), \
            'Nodes {}, {} not found in graph'.format(end_pn_1.pn, end_pn_2.pn)
        existing_link_group = self._get_link_group(end_pn_1, end_pn_2)
        if existing_link_group:
            new_link = existing_link_group.init_link(link_is_stable)
        else:
            new_link_group = self._init_new_link_group(end_pn_1, end_pn_2, link_is_stable)
            new_link = self.get_link_from_group(new_link_group, True)
        end_pn_1.pn.add_link_to_node_end(new_link, end_pn_1.end)
        end_pn_2.pn.add_link_to_node_end(new_link, end_pn_2.end)
        self.refresh_link_groups_and_links()
        return new_link

    @strictly_typed
    def disconnect_nodes(self, end_pn_1: EndOfPolarNode, end_pn_2: EndOfPolarNode) -> None:
        # removes 1 unstable link if exists
        pn_1, pn_2 = end_pn_1.pn, end_pn_2.pn
        link_group = self._get_link_group(end_pn_1, end_pn_2)
        unstable_links = link_group.unstable_links
        if not unstable_links:
            # there's nothing to disconnect
            return
        else:
            link = unstable_links.pop()
        pn_1.remove_link(link)
        pn_2.remove_link(link)
        link_group.remove_link(link)
        self.refresh_link_groups_and_links()

    @strictly_typed
    def insert_node(self, end_of_positive_up_node: EndOfPolarNode = None,
                    end_of_negative_down_node: EndOfPolarNode = None,
                    insertion_node: PolarNode = None,
                    make_pu_stable: bool = False, make_nd_stable: bool = False) -> PolarNode:
        # positive_up and negative_down for insertion_node, but their ends is
        if not end_of_positive_up_node:
            end_of_positive_up_node = self.inf_node_pu.end_nd
        if not end_of_negative_down_node:
            end_of_negative_down_node = self.inf_node_nd.end_pu
        if not insertion_node:
            insertion_node = self._init_node()
        existing_old_nodes_link_group = self._get_link_group(end_of_positive_up_node, end_of_negative_down_node)
        if existing_old_nodes_link_group:
            self.disconnect_nodes(end_of_positive_up_node, end_of_negative_down_node)
        self.connect_nodes(end_of_positive_up_node, insertion_node.end_pu, make_pu_stable)
        self.connect_nodes(end_of_negative_down_node, insertion_node.end_nd, make_nd_stable)
        return insertion_node

    @strictly_typed
    def find_node_coverage(self, start_end_of_node: EndOfPolarNode,
                           border_nodes: list[PolarNode] = None) -> PolarGraph:
        return self

    @strictly_typed
    def cut_subgraph(self, border_nodes: list[PolarNode]) -> PolarGraph:
        return self

    @strictly_typed
    def find_active_route(self, pn_1: PolarNode, pn_2: PolarNode) -> PolarGraph:
        return self

    @strictly_typed
    def find_all_routes(self, pn_1: PolarNode, pn_2: PolarNode) -> list[PolarGraph]:
        return [self]


@names_control
class PolarNode:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self) -> None:
        self._end_negative_down = EndOfPolarNode(self, End('nd'))
        self._end_positive_up = EndOfPolarNode(self, End('pu'))
        self._links_positive_up = set()
        self._links_negative_down = set()
        self.moves_group = PGMovesGroup()

    @property
    @strictly_typed
    def end_nd(self) -> EndOfPolarNode:
        return self._end_negative_down

    @property
    @strictly_typed
    def end_pu(self) -> EndOfPolarNode:
        return self._end_positive_up

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
        assert self in link.pns, 'Node not found in link ends'
        if node_end.is_negative_down:
            self._links_negative_down.add(link)
        else:
            self._links_positive_up.add(link)
        self.refresh_moves()

    @strictly_typed
    def remove_link(self, link: PGLink) -> None:
        assert self in link.pns, 'Node not found in link ends'
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
    def next_active_move_node(self, direction: End = End('nd')) -> PolarNode:
        active_move = self.moves_group.active_move
        if direction.is_negative_down:
            return active_move.node_negative_down
        else:
            return active_move.node_positive_up

    @strictly_typed
    def next_nodes(self, direction: End = End('nd')) -> list[PolarNode]:
        if direction.is_negative_down:
            next_links = self._links_negative_down
        else:
            next_links = self._links_positive_up
        return [link.opposite_pn(self) for link in next_links]

    @strictly_typed
    def switch_branch(self, move: PGMove) -> None:
        assert move in self.moves_group.moves, 'Move not found in node'
        self.moves_group.choice_move_activate(move)

    @strictly_typed
    def _get_move_by_defined_nodes(self, pn_1: PolarNode, pn_2: PolarNode) -> PGMove:
        assert not (pn_1 is pn_2), 'Nodes should be different'
        moves = [move for move in self.moves_group.moves
                 if {pn_1, pn_2} == {move.node_positive_up, move.node_negative_down}]
        assert moves, 'Move not found'
        return moves[0]

    @strictly_typed
    def get_move_by_nodes(self, pn_1: PolarNode = None, pn_2: PolarNode = None, fill_by_current: bool = False)\
            -> PGMove:
        positive_up_nodes = self.next_nodes(End('pu'))
        negative_down_nodes = self.next_nodes(End('nd'))
        neighborhood_nodes = set(positive_up_nodes) | set(negative_down_nodes)
        active_move = self.moves_group.active_move
        if (not pn_1) and pn_2:
            pn_1, pn_2 = pn_2, pn_1
        for pn in [pn_1, pn_2]:
            if pn:
                assert pn in neighborhood_nodes, 'Node {} not found in neighborhood_nodes'.format(pn)
        if bool(pn_1) & bool(pn_2):
            if ((pn_1 in positive_up_nodes) and (pn_2 in negative_down_nodes)) or \
                    ((pn_1 in negative_down_nodes) and (pn_2 in positive_up_nodes)):
                return self._get_move_by_defined_nodes(pn_1, pn_2)
            assert False, 'Given nodes at same side'
        elif pn_1:
            if pn_1 in positive_up_nodes:
                assert fill_by_current or (len(negative_down_nodes) == 1), 'Negative_down_node should be defined'
                return self._get_move_by_defined_nodes(pn_1, active_move.node_negative_down)
            else:
                assert fill_by_current or (len(positive_up_nodes) == 1), 'Positive_up_node should be defined'
                return self._get_move_by_defined_nodes(pn_1, active_move.node_positive_up)
        else:
            assert fill_by_current or (len(negative_down_nodes) == 1), 'Negative_down_node should be defined'
            assert fill_by_current or (len(positive_up_nodes) == 1), 'Positive_up_node should be defined'
            return active_move


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
            for mv in pg_00.inf_node_pu.moves_group.moves:
                print('mv +inf pos/neg = ', mv.node_positive_up, mv.node_negative_down)
            for mv in pg_00.inf_node_nd.moves_group.moves:
                print('mv -inf pos/neg = ', mv.node_positive_up, mv.node_negative_down)
            print('end of '+text)

        pg_00 = PolarGraph()
        print('pu infinity', pg_00.inf_node_pu)
        print('nd infinity', pg_00.inf_node_nd)
        # check_inf_moves('before all connections: ')
        # print('Infinity node', pg._infinity_node_positive_up) #
        pg_1 = PolarNode(pg_00, name='PolarNode_pg_1')
        # check_inf_moves('after pg_1 creation: ')
        # print('take by name', PolarNode.get_inst_by_name('PolarNode_test_2'))
        print('pg_1 name = ', pg_1.name)
        pg_2 = PolarNode(pg_00, name='PolarNode_pg_2')
        pg_3 = PolarNode(pg_00, name='PolarNode_pg_3')
        pg_4 = PolarNode(pg_00, name='PolarNode_pg_4')
        pg_5 = PolarNode(pg_00, name='PolarNode_pg_5')
        # check_inf_moves('after pg_1-5 creation: ')
        print('pg1 links neg down =', pg_1.links_negative_down)
        pg_1.connect_to_its_end(pg_2, its_end=End('nd'), remove_infinity=False)
        # check_inf_moves('after connect pg_1 pg_2: ')
        pg_1.connect_to_its_end(pg_4, remove_infinity=False)
        pg_3.connect_to_its_end(pg_1)
        pg_5.connect_to_its_end(pg_1)

        # print('get link = ', pg.get_link_from_group(pg_1, pg_5))

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
            print('link', lnk.opposite_pn(curr_node))

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

        # pg.inf_node_pu.switch_branch(pg_2)
        # pg.inf_node_nd.switch_branch(pg_3)

        print('active nodes: ', pg_1.moves_group.active_move.node_positive_up,
              pg_1.moves_group.active_move.node_negative_down)

        print('next nd for pg_1', pg_1.next_active_move_node())
        print('next pu for pg_1', pg_1.next_active_move_node(End('pu')))
        print('all nd for pg_1', pg_1.next_nodes())
        print('all pu for pg_1', pg_1.next_nodes(End('pu')))
        print('next nd for pg_2', pg_2.next_active_move_node())
        print('next nd for pg_3', pg_3.next_active_move_node())
        print('next pu for nd inf', pg_00.inf_node_nd.next_active_move_node(End('pu')))
        print('next nd for pu inf', pg_00.inf_node_pu.next_active_move_node())
        print('next pu for pu inf', pg_00.inf_node_pu.next_active_move_node(End('pu')))
        print('next nd for nd inf', pg_00.inf_node_nd.next_active_move_node())
        print('all nd for pu inf', pg_00.inf_node_pu.next_nodes())

    if test == 'test_2':

        def print_active_moves(pg_):
            for node_ in pg_.nodes:
                print('active move = ', node_.moves_group.active_move)

        pg_00 = PolarGraph()
        print('pg.inf_node_pu ', pg_00.inf_node_pu)
        print('pg.inf_node_nd ', pg_00.inf_node_nd)
        pn_01 = pg_00.insert_node(make_pu_stable=True, make_nd_stable=True)  # make_nd_stable=True
        # pn_00 = copy(pn_01)
        pn_02 = pg_00.insert_node(end_of_negative_down_node=pn_01.end_pu)
        pn_03 = pg_00.insert_node(end_of_negative_down_node=pn_01.end_pu)
        pn_04 = pg_00.insert_node(end_of_positive_up_node=pn_01.end_nd)
        pn_05 = pg_00.insert_node(end_of_positive_up_node=pn_01.end_nd)
        print('pn_01 ', pn_01)
        print('pg nodes ', pg_00.nodes)
        # print_active_moves(pg)
        pn_01.switch_branch(pn_01.get_move_by_nodes(pn_02, pn_04))  # save_second_current=True
        ms = PGMovesState(pg_00)
        # print_active_moves(pg)
        print('pg links len ', len(pg_00.links))
        print('pg links ', pg_00.links)
        print('pn_01 next all nd ', pn_01.next_nodes())
        print('pn_01 next all pu ', pn_01.next_nodes(End('pu')))

        print('before switch :')
        print('pn_01 next active nd ', pn_01.next_active_move_node())
        print('pn_01 next active pu ', pn_01.next_active_move_node(End('pu')))

        pn_01.switch_branch(pn_01.get_move_by_nodes(pn_03, pn_05))
        print('after switch :')
        print('pn_01 next active nd ', pn_01.next_active_move_node())
        print('pn_01 next active pu ', pn_01.next_active_move_node(End('pu')))
        ms.reset_state()
        print('after reset :')
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

    if test == 'test_3':

        pn_01 = PolarNode()
        print(End('nd') == 'pu')
        pe_01 = EndOfPolarNode(pn_01, End('nd'))
        pe_02 = EndOfPolarNode(pn_01, End('pu'))
        pe_03 = EndOfPolarNode(pn_01, End('nd'))
        print(pe_01, pe_01.other_pn_end)
        print(pe_02 == pe_01.other_pn_end)
        print('eq = ', pe_03 == pe_01)
        print('in = ', pe_03 in {pe_01})
        print({pe_02, pe_01.other_pn_end})
        print(pe_02 is pe_01.other_pn_end)
        print('eq 2 = ', pe_03 == pn_01.end_nd)

    if test == 'test_4':

        pg_00 = PolarGraph()
        print('pg.inf_node_pu ', pg_00.inf_node_pu)
        print('pg.inf_node_nd ', pg_00.inf_node_nd)
        pn_01 = pg_00.insert_node()  # make_nd_stable=True
        # pn_00 = copy(pn_01)
        pn_02 = pg_00.insert_node(end_of_negative_down_node=pn_01.end_pu, make_nd_stable=True)
        pg_00.connect_nodes(pn_01.end_pu, pn_02.end_nd)
        pg_00.connect_nodes(pn_01.end_pu, pn_02.end_nd)
        pn_03 = pg_00.insert_node(pn_02.end_nd, pn_01.end_pu)
        pn_04 = pg_00.insert_node(pn_02.end_nd, pn_01.end_pu)
        print('pn_01 ', pn_01)
        print('pg nodes ', pg_00.nodes)
        print('pg links len ', len(pg_00.links))
        print('pg links ', pg_00.links)
        print('pn_01 next all nd ', pn_01.next_nodes())
        print('pn_01 next all pu ', pn_01.next_nodes(End('pu')))
        print('pn_01 next active nd ', pn_01.next_active_move_node())
        print('pn_01 next active pu ', pn_01.next_active_move_node(End('pu')))

    if test == 'test_5':

        pg_00 = PolarGraph()
        print('pg.inf_node_pu ', pg_00.inf_node_pu)
        print('pg.inf_node_nd ', pg_00.inf_node_nd)
        pn_01 = pg_00.insert_node()  # make_nd_stable=True
        # pn_00 = copy(pn_01)
        pg_00.connect_nodes(pn_01.end_nd, pg_00.inf_node_pu.end_nd)
        print('pn_01 ', pn_01)
        print('pg nodes ', pg_00.nodes)
        print('pg links len ', len(pg_00.links))
        print('pg links ', pg_00.links)
        print('pn_01 next all nd ', pn_01.next_nodes())
        print('pn_01 next all pu ', pn_01.next_nodes(End('pu')))
        print('pn_01 next active nd ', pn_01.next_active_move_node())
        print('pn_01 next active pu ', pn_01.next_active_move_node(End('pu')))

    if test == 'test_6':

        pg_00 = PolarGraph()
        print('pg.inf_node_pu ', pg_00.inf_node_pu)
        print('pg.inf_node_nd ', pg_00.inf_node_nd)
        pn_01 = pg_00.insert_node()  # make_nd_stable=True
        # pn_00 = copy(pn_01)
        pn_02 = pg_00.insert_node(end_of_negative_down_node=pn_01.end_pu, make_nd_stable=True)
        # pg.connect_nodes(pn_01.end_nd, pn_02.end_pu)
        # pg.connect_nodes(pn_01.end_pu, pn_02.end_nd)
        # pn_03 = pg.insert_node(pn_02.end_nd, pn_01.end_pu)
        # pn_04 = pg.insert_node(pn_02.end_nd, pn_01.end_pu)
        print('pn_01 ', pn_01)
        print('pg nodes ', pg_00.nodes)
        print('pg links len ', len(pg_00.links))
        print('pg links ', pg_00.links)
        print('pn_01 next all nd ', pn_01.next_nodes())
        print('pn_01 next all pu ', pn_01.next_nodes(End('pu')))
        print('pn_01 next active nd ', pn_01.next_active_move_node())
        print('pn_01 next active pu ', pn_01.next_active_move_node(End('pu')))

        # pn_011 = deepcopy(pn_01)
        # pg.connect_nodes(pn_01.end_pu, pn_02.end_nd)
        # print('pn_01 next all nd ', pn_01.next_nodes())
        # print('pn_01 next all pu ', pn_01.next_nodes(End('pu')))
        # print('pn_01 next active nd ', pn_01.next_active_move_node())
        # print('pn_01 next active pu ', pn_01.next_active_move_node(End('pu')))
        # print('pn_011 next all nd ', pn_011.next_nodes())
        # print('pn_011 next all pu ', pn_011.next_nodes(End('pu')))
        # print('pn_011 next active nd ', pn_011.next_active_move_node())
        # print('pn_011 next active pu ', pn_011.next_active_move_node(End('pu')))

        pg_10 = deepcopy(pg_00)
        print('pg_10 nodes ', pg_10.nodes)
        print('pg_10 links len ', len(pg_10.links))
        print('pg_10 links ', pg_10.links)
        print('pg_10 nodes ', pg_10.nodes[0] is pg_00.nodes[0])
