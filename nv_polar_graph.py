from __future__ import annotations
from copy import copy, deepcopy
from collections import deque
from collections.abc import Iterable
# from itertools import product

from nv_typing import *
from nv_names_control import names_control
from nv_string_set_class import StringSet


class End(StringSet):

    @strictly_typed
    def __init__(self, str_end: str) -> None:
        super().__init__([['negative_down', 'nd'], ['positive_up', 'pu']], str_end)

    @property
    @strictly_typed
    def is_negative_down(self) -> bool:
        return self == 'nd'

    @property
    @strictly_typed
    def is_positive_up(self) -> bool:
        return self == 'pu'

    @property
    @strictly_typed
    def opposite_end(self) -> End:
        if self.is_negative_down:
            return End('pu')
        else:
            return End('nd')


class PNEnd:

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
    def other_pn_end(self) -> PNEnd:
        return PNEnd(self.pn, self.end.opposite_end)

    @strictly_typed
    def __eq__(self, other: PNEnd) -> bool:
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

    @strictly_typed
    def __init__(self, ni: NodeInterface) -> None:
        self._ni = ni
        self._moves = set()
        self._move_by_link = dict()

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.ni)

    @property
    @strictly_typed
    def ni(self) -> NodeInterface:
        return self._ni

    @strictly_typed
    def get_move_by_link(self, link: PGLink) -> PGMove:
        return self._move_by_link[link]

    @property
    @strictly_typed
    def moves(self) -> set[PGMove]:
        return copy(self._moves)

    @property
    @strictly_typed
    def active_move(self) -> Optional[PGMove]:
        active_moves = set(filter(lambda item: item.active, self._moves))
        assert len(active_moves) <= 1, 'Only <= 1 Move should be active'
        if active_moves:
            return active_moves.pop()

    @property
    @strictly_typed
    def inactive_moves(self) -> Optional[set[PGMove]]:
        if not self.moves:
            return
        return copy(self.moves - {self.active_move})

    @strictly_typed
    def choice_move_activate(self, move: PGMove) -> None:
        assert move in self.moves, 'Move not found in MoveGroup'
        self._deactivate_all_moves()
        move.active = True

    def refresh_moves(self):
        self._clear()
        for link in self.ni.links:
            # print('Refresh_moves, for link', link)
            new_move = PGMove(self.ni, link)
            self._add_move(new_move)
            self._add_move_by_link(link, new_move)
        self._random_move_activate()

    @strictly_typed
    def _add_move(self, move: PGMove) -> None:
        move.active = False
        self._moves.add(move)

    @strictly_typed
    def _add_move_by_link(self, link: PGLink, move: PGMove) -> None:
        self._move_by_link[link] = move

    def _deactivate_all_moves(self):
        for move in self.moves:
            move.active = False

    def _random_move_activate(self):
        # print('In random move activate, self = {}, curr set = {}'.format(self, self.moves))
        self._deactivate_all_moves()
        if self.moves:
            move_random = self.moves.pop()
            move_random.active = True

    def _clear(self):
        self._moves.clear()
        self._move_by_link.clear()


class PGMove:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self, ni: NodeInterface, link: PGLink) -> None:
        self._link = link
        self._ni = ni
        self._active = False

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.ni, self.link)

    @property
    @strictly_typed
    def link(self) -> PGLink:
        return self._link

    @property
    @strictly_typed
    def ni(self) -> NodeInterface:
        return self._ni

    @property
    @strictly_typed
    def pn(self) -> PolarNode:
        return self.ni.pn

    @property
    @strictly_typed
    def active(self) -> bool:
        return self._active

    @active.setter
    @strictly_typed
    def active(self, value: bool) -> None:
        self._active = value


class PGLinkGroup:

    @strictly_typed
    def __init__(self, end_pn_1: PNEnd, end_pn_2: PNEnd,
                 first_link_is_stable: bool = False) -> None:
        self.end_pns = {end_pn_1, end_pn_2}
        self._links = set()
        self.init_link(first_link_is_stable)

    def __repr__(self):
        end_pns_tuple = tuple(self.end_pns)
        return '{}({}, {})'.format(self.__class__.__name__, end_pns_tuple[0], end_pns_tuple[1])

    @property
    @strictly_typed
    def end_pns(self) -> set[PNEnd]:
        return copy(self._end_pns)

    @end_pns.setter
    @strictly_typed
    def end_pns(self, value: Iterable[PNEnd]) -> None:
        end_pn_set = set(value)
        assert len(end_pn_set) == 2, 'Count of ends for linking should be == 2'
        end_pn_1, end_pn_2 = tuple(end_pn_set)
        assert end_pn_1.pn != end_pn_2.pn, 'Cannot connect node to itself'
        self._end_pns = end_pn_set

    @strictly_typed
    def other_end(self, first_end: PNEnd) -> PNEnd:
        assert first_end in self.end_pns, 'End of node not found in end_pns'
        return (self.end_pns - {first_end}).pop()

    @strictly_typed
    def rebind_node(self, old_end_pn: PNEnd, new_end_pn: PNEnd) -> None:
        sec_node = self.other_end(old_end_pn)
        self.end_pns = (sec_node, new_end_pn)

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
            return self.links - {stable_link}
        else:
            return self.links

    @strictly_typed
    def get_link(self, arbitrary_stable: bool = True, stable: bool = False) -> Optional[PGLink]:
        # gets link by stability
        if self.links:
            if arbitrary_stable:
                return self.links.pop()
            elif stable:
                return self.stable_link
            else:
                unstable_links = self.unstable_links
                if unstable_links:
                    return unstable_links.pop()

    @property
    @strictly_typed
    def count_of_links(self) -> int:
        return len(self.links)

    @property
    @strictly_typed
    def pns(self) -> set[PolarNode]:
        end_pn_1, end_pn_2 = tuple(self.end_pns)
        return {end_pn_1.pn, end_pn_2.pn}

    @strictly_typed
    def end_of_pn(self, pn: PolarNode) -> End:
        assert pn in self.pns, 'Polar node not found'
        for end_pn in self.end_pns:
            if end_pn.pn is pn:
                return end_pn.end

    @strictly_typed
    def init_link(self, init_stable: bool = False) -> PGLink:
        assert not (self.stable_link and init_stable), 'Only 1 stable link may be between same nodes'
        new_link = PGLink(self, init_stable)
        self._links.add(new_link)
        return new_link

    @strictly_typed
    def remove_link(self, link: PGLink) -> None:
        self._links.remove(link)


class PGLink:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self, link_group: PGLinkGroup, is_stable: bool = False) -> None:
        self.stable = is_stable
        self._link_group = link_group

    def __repr__(self):
        stable_str = 'stable' if self.stable else ''
        end_pns_tuple = tuple(self.end_pns)
        return '{}({}, {}, {})'.format(self.__class__.__name__, end_pns_tuple[0], end_pns_tuple[1], stable_str)

    @property
    @strictly_typed
    def link_group(self) -> PGLinkGroup:
        return self._link_group

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
    def end_pns(self) -> set[PNEnd]:
        return self.link_group.end_pns

    @property
    @strictly_typed
    def pns(self) -> set[PolarNode]:
        return self.link_group.pns

    @strictly_typed
    def opposite_pn(self, current_pn: PolarNode) -> PolarNode:
        assert current_pn in self.pns, 'Current end not found'
        return (self.pns - {current_pn}).pop()


class NodeInterface:
    @strictly_typed
    def __init__(self, end_pn: PNEnd) -> None:
        self._end_pn = end_pn
        self._links = set()
        self._moves_group = PGMovesGroup(self)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.end_pn)

    @property
    @strictly_typed
    def end_pn(self) -> PNEnd:
        return self._end_pn

    @end_pn.setter
    @strictly_typed
    def end_pn(self, value: PNEnd) -> None:
        self._end_pn = value

    @property
    @strictly_typed
    def pn(self) -> PolarNode:
        return self.end_pn.pn

    @property
    @strictly_typed
    def end(self) -> End:
        return self.end_pn.end

    @property
    @strictly_typed
    def links(self) -> set[PGLink]:
        # print('IN get links of {}, got {}'.format(self, self._links))
        return copy(self._links)

    @property
    @strictly_typed
    def link_groups(self) -> set[PGLinkGroup]:
        # print('IN get links of {}, got {}'.format(self, self._links))
        return set(link.link_group for link in self._links)

    @property
    @strictly_typed
    def moves_group(self) -> PGMovesGroup:
        return self._moves_group

    @property
    @strictly_typed
    def is_empty(self) -> bool:
        return not self._links

    @strictly_typed
    def add_link(self, link: PGLink) -> None:
        self._links.add(link)
        self._refresh_ni_moves()
        # print('In add link for {}, new link list {}'.format(self, self._links))

    @strictly_typed
    def remove_link(self, link: PGLink) -> None:
        self._links.remove(link)
        # print('In remove link for {}, new link list {}'.format(self, self._links))
        self._refresh_ni_moves()

    def _refresh_ni_moves(self):
        self.moves_group.refresh_moves()

    @property
    @strictly_typed
    def next_active_node(self) -> PolarNode:
        active_move = self.moves_group.active_move
        return active_move.link.opposite_pn(self.pn)

    @property
    @strictly_typed
    def next_nodes(self) -> set[PolarNode]:
        return {link.opposite_pn(self.pn) for link in self.links}

    @property
    @strictly_typed
    def next_ends(self) -> set[PNEnd]:
        return {link.link_group.other_end(self.end_pn) for link in self.links}


@names_control
class PolarNode:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self) -> None:
        self._end_negative_down, self._end_positive_up = PNEnd(self, End('nd')), PNEnd(self, End('pu'))
        self._interface_negative_down, self._interface_positive_up = \
            NodeInterface(self.end_nd), NodeInterface(self.end_pu)
        self._ni_by_end = {self._end_negative_down: self._interface_negative_down,
                           self._end_positive_up: self._interface_positive_up}

    @property
    @strictly_typed
    def count_side_connected(self) -> int:
        return int(not self.ni_nd.is_empty) + int(not self.ni_pu.is_empty)

    @strictly_typed
    def get_ni_by_end(self, end_pn: PNEnd) -> NodeInterface:
        return self._ni_by_end[end_pn]

    @property
    @strictly_typed
    def ni_nd(self) -> NodeInterface:
        return self._interface_negative_down

    @property
    @strictly_typed
    def ni_pu(self) -> NodeInterface:
        return self._interface_positive_up

    @property
    @strictly_typed
    def end_nd(self) -> PNEnd:
        return self._end_negative_down

    @property
    @strictly_typed
    def end_pu(self) -> PNEnd:
        return self._end_positive_up

    @strictly_typed
    def add_link_to_node_end(self, link: PGLink, node_end: End = End('nd')) -> None:
        assert self in link.pns, 'Node not found in link ends'
        if node_end.is_negative_down:
            self.ni_nd.add_link(link)
        else:
            self.ni_pu.add_link(link)

    @strictly_typed
    def remove_link_from_pn(self, link: PGLink) -> None:
        assert self in link.pns, 'Node not found in link ends'
        if link in self.ni_nd.links:
            self.ni_nd.remove_link(link)
            return
        if link in self.ni_pu.links:
            self.ni_pu.remove_link(link)
            return
        assert False, 'Link not found in node'

    @strictly_typed
    def switch_move_branch(self, move: PGMove) -> None:
        if move in self.ni_nd.moves_group.moves:
            self.ni_nd.moves_group.choice_move_activate(move)
            return
        if move in self.ni_pu.moves_group.moves:
            self.ni_pu.moves_group.choice_move_activate(move)
            return
        assert False, 'Move not found in node'

    @strictly_typed
    def next_active_direction_node(self, direction: End = End('nd')) -> PolarNode:
        if direction.is_negative_down:
            return self.ni_nd.next_active_node
        else:
            return self.ni_pu.next_active_node

    @strictly_typed
    def next_direction_nodes(self, direction: End = End('nd')) -> set[PolarNode]:
        if direction.is_negative_down:
            return self.ni_nd.next_nodes
        else:
            return self.ni_pu.next_nodes


class PGGraphMovesState:

    @strictly_typed
    def __init__(self, pg: BasePolarGraph) -> None:
        self._moves = []
        self.save_state(pg)

    @strictly_typed
    def save_state(self, pg: BasePolarGraph) -> None:
        for pn in pg.nodes:
            ni_nd, ni_pu = pn.ni_nd, pn.ni_pu
            nd_active_move, pu_active_move = ni_nd.moves_group.active_move, ni_pu.moves_group.active_move
            if nd_active_move:
                self._moves.append(ni_nd.moves_group.active_move)
            if pu_active_move:
                self._moves.append(ni_pu.moves_group.active_move)

    @strictly_typed
    def reset_state(self) -> None:
        for move in self._moves:
            # print('Reset state in move ', move)
            move.pn.switch_move_branch(move)


@names_control
class PolarGraph:

    def __init__(self):
        self._nodes = set()
        self._border_ends = set()
        self._link_groups = set()
        self._links = set()

    @strictly_typed
    def _init_node(self) -> PolarNode:
        node = PolarNode()
        self._nodes.add(node)
        return node

    @property
    @strictly_typed
    def nodes(self) -> set[PolarNode]:
        return copy(self._nodes)

    @property
    @strictly_typed
    def border_nodes(self) -> set[PolarNode]:
        return set([end.pn for end in self._border_ends])

    @property
    @strictly_typed
    def border_ends(self) -> set[PNEnd]:
        return self._border_ends

    @border_ends.setter
    @strictly_typed
    def border_ends(self, value: Iterable[PNEnd]) -> None:
        self._border_ends = set(value)

    @property
    @strictly_typed
    def link_groups(self) -> set[PGLinkGroup]:
        return copy(self._link_groups)

    @property
    @strictly_typed
    def links(self) -> set[PGLink]:
        return copy(self._links)

    @strictly_typed
    def moves_activate_by_ends(self, end_pn_1: PNEnd, end_pn_2: PNEnd, pn_only_for: PolarNode = None) -> None:
        link_group = self._get_link_group_by_ends(end_pn_1, end_pn_2)
        if link_group:
            # print('Link group was found')
            for end_pn in link_group.end_pns:
                # print('For end pn ', end_pn)
                pn_get = end_pn.pn
                if pn_only_for and not (pn_get is pn_only_for):
                    continue
                ni = pn_get.get_ni_by_end(end_pn)
                link = link_group.get_link()
                move = ni.moves_group.get_move_by_link(link)
                ni.moves_group.choice_move_activate(move)

    @strictly_typed
    def connect_nodes(self, end_pn_1: PNEnd, end_pn_2: PNEnd,
                      link_is_stable: bool = False) -> PGLink:
        assert not (end_pn_1.pn is end_pn_2.pn), 'Cannot connect node {} to himself'.format(end_pn_1.pn)
        assert {end_pn_1.pn, end_pn_2.pn} <= set(self.nodes), \
            'Nodes {}, {} not found in graph'.format(end_pn_1.pn, end_pn_2.pn)
        existing_link_group = self._get_link_group_by_ends(end_pn_1, end_pn_2)
        if existing_link_group:
            new_link = existing_link_group.init_link(link_is_stable)
        else:
            new_link_group = self._init_new_link_group(end_pn_1, end_pn_2, link_is_stable)
            new_link = new_link_group.get_link()
            # new_link = self._get_link_from_group(new_link_group, True)
        end_pn_1.pn.add_link_to_node_end(new_link, end_pn_1.end)
        end_pn_2.pn.add_link_to_node_end(new_link, end_pn_2.end)
        self._refresh_link_groups_and_links()
        return new_link

    @strictly_typed
    def disconnect_nodes(self, end_pn_1: PNEnd, end_pn_2: PNEnd) -> None:
        # removes 1 unstable link if exists
        pn_1, pn_2 = end_pn_1.pn, end_pn_2.pn
        link_group = self._get_link_group_by_ends(end_pn_1, end_pn_2)
        unstable_links = link_group.unstable_links
        if not unstable_links:
            # there's nothing to disconnect
            return
        else:
            link = unstable_links.pop()
        pn_1.remove_link_from_pn(link)
        pn_2.remove_link_from_pn(link)
        link_group.remove_link(link)
        self._refresh_link_groups_and_links()

    @strictly_typed
    def insert_node(self, end_of_positive_up_node: PNEnd,
                    end_of_negative_down_node: PNEnd,
                    insertion_node: PolarNode = None,
                    make_pu_stable: bool = False, make_nd_stable: bool = False) -> PolarNode:
        # positive_up and negative_down for insertion_node, but their ends is
        if not insertion_node:
            insertion_node = self._init_node()
        existing_old_nodes_link_group = self._get_link_group_by_ends(end_of_positive_up_node, end_of_negative_down_node)
        if existing_old_nodes_link_group:
            self.disconnect_nodes(end_of_positive_up_node, end_of_negative_down_node)
        self.connect_nodes(end_of_positive_up_node, insertion_node.end_pu, make_pu_stable)
        self.connect_nodes(end_of_negative_down_node, insertion_node.end_nd, make_nd_stable)
        return insertion_node

    @strictly_typed
    def find_node_coverage(self, start_end_of_node: PNEnd,
                           additional_border_nodes: Iterable[PolarNode] = None) -> PolarGraph:
        assert start_end_of_node.pn in self.nodes, 'Begin node for find coverage not found'
        common_border_nodes = self.border_nodes
        common_border_nodes.add(start_end_of_node.pn)
        if additional_border_nodes:
            assert all([ab_pn in self.nodes for ab_pn in additional_border_nodes]), 'Border node not found'
            common_border_nodes |= set(additional_border_nodes)
        coverage_pg = PolarGraph()
        found_nodes = {start_end_of_node.pn}
        found_link_groups = set()
        found_enter_ends = set()
        found_out_ends = {start_end_of_node}
        found_border_ends = {start_end_of_node}
        ends_stack = deque([start_end_of_node])  # : list[PNEnd]
        while ends_stack:
            current_ends_stack = copy(ends_stack)
            for end in current_ends_stack:
                ends_stack.popleft()
                ni: NodeInterface = end.pn.get_ni_by_end(end)
                found_link_groups.update(ni.link_groups)
                next_enter_ends = ni.next_ends
                for next_enter_end in next_enter_ends:
                    node = next_enter_end.pn
                    found_nodes.add(node)
                    found_enter_ends.add(next_enter_end)
                    if node in common_border_nodes:
                        found_border_ends.add(next_enter_end)
                    else:
                        assert not (next_enter_end in found_out_ends), \
                            'Cycle was found in node_end {}'.format(next_enter_end)
                        if node.count_side_connected == 2:
                            out_end = next_enter_end.other_pn_end
                            found_out_ends.add(out_end)
                            ends_stack.append(out_end)
                        # assert node not in found_nodes, 'Cycle was found, node: {}'.format(node)
                    # found_nodes.add(node)
        print('Found nodes: ', found_nodes)
        print('Found enter ends: ', found_enter_ends)
        print('Found border ends: ', found_border_ends)
        print('Found link groups: ', found_link_groups)
        # coverage_pg.nodes =
        return coverage_pg

    @strictly_typed
    def cut_subgraph(self, border_nodes: list[PolarNode]) -> PolarGraph:
        return self

    @strictly_typed
    def find_active_route(self, pn_1: PolarNode, pn_2: PolarNode) -> PolarGraph:
        return self

    @strictly_typed
    def find_all_routes(self, pn_1: PolarNode, pn_2: PolarNode) -> list[PolarGraph]:
        return [self]

    def _refresh_link_groups_and_links(self):
        self._links.clear()
        for link_group in self.link_groups:
            if link_group.count_of_links == 0:
                self._link_groups.remove(link_group)
            else:
                self._links |= link_group.links

    @strictly_typed
    def _get_link_group_by_ends(self, end_pn_1: PNEnd, end_pn_2: PNEnd) -> Optional[PGLinkGroup]:
        link_groups = [link_group for link_group in self.link_groups
                       if {end_pn_1, end_pn_2} == set(link_group.end_pns)]
        assert len(link_groups) <= 1, '2 link_groups with equal nodes and ends was found'
        if link_groups:
            return link_groups[0]

    def _check_cycles(self):
        pass

    @strictly_typed
    def _check_new_link_group_existing_possibility(self, end_pn_1: PNEnd, end_pn_2: PNEnd) -> bool:
        return not bool(self._get_link_group_by_ends(end_pn_1, end_pn_2))

    @strictly_typed
    def _init_new_link_group(self, end_pn_1: PNEnd, end_pn_2: PNEnd,
                             first_link_is_stable: bool = False) -> PGLinkGroup:
        assert self._check_new_link_group_existing_possibility(end_pn_1, end_pn_2), 'Link_group already exists'
        new_link_group = PGLinkGroup(end_pn_1, end_pn_2, first_link_is_stable)
        self._link_groups.add(new_link_group)
        return new_link_group


@names_control
class BasePolarGraph(PolarGraph):

    def __init__(self):
        super().__init__()

        self._infinity_node_positive_up = self._init_node()
        self._infinity_node_negative_down = self._init_node()
        self.border_ends = {self.inf_node_pu.end_nd, self.inf_node_nd.end_pu}

    @property
    @strictly_typed
    def inf_node_pu(self) -> PolarNode:
        return self._infinity_node_positive_up

    @property
    @strictly_typed
    def inf_node_nd(self) -> PolarNode:
        return self._infinity_node_negative_down


# class AttributeTuple:
#     def __init__(self, node_type, node_name, node_value):
#         self.node_type = node_type
#         self.node_name = node_name
#         self.node_value = node_value
#
#
# class AttributeNode(PolarNode):
#
#     @strictly_typed
#     def __init__(self, node_type: OneOfString(['title', 'splitter', 'value']), node_name: str = '',
#                  node_value: Any = None) -> None:
#         super().__init__()
#         self.content = AttributeTuple(node_type, node_name, node_value)
#
#     @property
#     def value(self):
#         return self.content.node_value
#
#     @value.setter
#     def value(self, val):
#         self.content.node_value = val
#
#
# class AttributeGraph(BasePolarGraph):
#
#     def __init__(self):
#         super().__init__()
#         self._splitters_last_nodes = []  # list[an]
#         self._associations = {}  # {(split_an, str_val): derived_an}
#
#     @strictly_typed
#     def associate(self, splitter_an: AttributeNode, splitter_str_value: str, derived_an: AttributeNode) -> None:
#         assert splitter_an in self._nodes, 'Splitter not found in nodes list'
#         assert splitter_an.content.node_type == 'splitter', 'Can be only splitter associated'
#         assert splitter_str_value in splitter_an.content.node_value, 'Splitter str-value not found in values list'
#         self._associations[(splitter_an, splitter_str_value)] = derived_an
#
#     @strictly_typed
#     def _add_node(self, an: AttributeNode, to_splitter: AttributeNode = None, associated_splitter_value: str = '',
#                   out_splitter: bool = False) -> None:
#         self._nodes.append(an)
#         if len(self._nodes) == 1:
#             return
#         last_node = self._nodes[-1]
#         if to_splitter:
#             assert to_splitter in self._nodes, 'Splitter not found in nodes'
#             if last_node != to_splitter:
#                 self._splitters_last_nodes.append(last_node)
#             an.connect_to_its_end(to_splitter)
#             self.associate(to_splitter, associated_splitter_value, an)
#         elif out_splitter:
#             for splitters_last_node in self._splitters_last_nodes:
#                 an.connect_to_its_end(splitters_last_node)
#             self._splitters_last_nodes.clear()
#         else:
#             an.connect_to_its_end(last_node)
#
#     @strictly_typed
#     def add_typed_node(self, node_type: OneOfString(['title', 'splitter', 'value']), node_name: str,
#                        to_splitter: AttributeNode = None, associated_splitter_value: str = '') -> None:
#         an = AttributeNode(node_type, node_name)
#         self._add_node(an, to_splitter, associated_splitter_value)
#
#     @strictly_typed
#     def set_node_value(self, value_name: str, value: Any) -> None:
#         node_found = False
#         for node in self._nodes:
#             if (node.content.node_type in ['value', 'splitter']) and (node.content.node_name == value_name):
#                 if node.content.node_type == 'splitter':
#                     assert isinstance(value, Iterable), 'Need iterable value for splitter'
#                     for val in value:
#                         assert type(val) == str, 'Values in splitter should be str'
#                 node.content.node_value = value
#                 return
#         assert node_found, 'Node for setting value is not found'
#
#     @strictly_typed
#     def last_splitter(self) -> Optional[AttributeNode]:
#         for node in reversed(self._nodes):
#             if node.content.node_type == 'splitter':
#                 return node
#
#     @strictly_typed
#     def switch_splitter(self, splitter_name: str, to_splitter_str_value: str) -> None:
#         node_found = False
#         for node in self._nodes:
#             if (node.content.node_type == 'splitter') and (node.content.node_name == splitter_name):
#                 node_found = True
#                 node.switch_move_branch(self._associations[(node, to_splitter_str_value)])
#         assert node_found, 'Node for setting value is not found'
#
#     @strictly_typed
#     def get_linear_list(self) -> list[AttributeTuple]:
#         pass


if __name__ == '__main__':

    test = 'test_2'
    if test == 'test_1':
        pass

    if test == 'test_2':

        # def print_active_moves(pg_):
        #     for node_ in pg_.nodes:
        #         print('active move = ', node_._moves_group.active_move)

        pg_00 = BasePolarGraph()
        print('pg.inf_node_pu ', pg_00.inf_node_pu)
        print('pg.inf_node_nd ', pg_00.inf_node_nd)
        print('links in pg ', pg_00.links)
        print('moves of inf_pu pu', pg_00.inf_node_pu.ni_pu.moves_group.moves)
        print('moves of inf_pu nd', pg_00.inf_node_pu.ni_nd.moves_group.moves)

        pn_01 = pg_00.insert_node(pg_00.inf_node_pu.end_nd, pg_00.inf_node_nd.end_pu,
                                  make_pu_stable=True, make_nd_stable=True)
        # pn_00 = copy(pn_01)
        pn_02 = pg_00.insert_node(pg_00.inf_node_pu.end_nd, pn_01.end_pu)
        pn_03 = pg_00.insert_node(pg_00.inf_node_pu.end_nd, pn_01.end_pu)
        pn_04 = pg_00.insert_node(pn_01.end_nd, pg_00.inf_node_nd.end_pu)
        pn_05 = pg_00.insert_node(pn_01.end_nd, pg_00.inf_node_nd.end_pu)
        print('pn_01 ', pn_01)
        print('pg nodes ', pg_00.nodes)
        print('pg.inf_node_pu ', pg_00.inf_node_pu)
        print('pg.inf_node_nd ', pg_00.inf_node_nd)
        print('links in pg ', pg_00.links)
        print('len of links in pg ', len(pg_00.links))
        print('moves of inf_pu pu', pg_00.inf_node_pu.ni_pu.moves_group.moves)
        print('moves of inf_pu nd', pg_00.inf_node_pu.ni_nd.moves_group.moves)
        print('active move of inf_pu pu', pg_00.inf_node_pu.ni_pu.moves_group.active_move)
        print('active move of inf_pu nd', pg_00.inf_node_pu.ni_nd.moves_group.active_move)
        print('next nodes of inf_pu pu', pg_00.inf_node_pu.ni_pu.next_nodes)
        print('next nodes of inf_pu nd', pg_00.inf_node_pu.ni_nd.next_nodes)
        print('Before activation')
        ms = PGGraphMovesState(pg_00)
        # print('active node of inf_pu pu', pg_00.inf_node_pu.ni_pu.next_active_node)
        print('active node of inf_pu nd', pg_00.inf_node_pu.ni_nd.next_active_node)
        print('active node of pn_01 pu', pn_01.ni_pu.next_active_node)
        pg_00.moves_activate_by_ends(pn_01.end_pu, pg_00.inf_node_pu.end_nd)
        print('After activation')
        # print('active node of inf_pu pu', pg_00.inf_node_pu.ni_pu.next_active_node)
        print('active node of inf_pu nd', pg_00.inf_node_pu.ni_nd.next_active_node)
        print('active node of pn_01 pu', pn_01.ni_pu.next_active_node)
        print('After reset')
        ms.reset_state()
        # print('active node of inf_pu pu', pg_00.inf_node_pu.ni_pu.next_active_node)
        print('active node of inf_pu nd', pg_00.inf_node_pu.ni_nd.next_active_node)
        print('active node of pn_01 pu', pn_01.ni_pu.next_active_node)

        pg_00.find_node_coverage(pn_02.end_nd)

    if test == 'test_3':
        pn_01 = PolarNode()
        print(End('nd') == 'pu')
        pe_01 = PNEnd(pn_01, End('nd'))
        pe_02 = PNEnd(pn_01, End('pu'))
        pe_03 = PNEnd(pn_01, End('nd'))
        print(pe_01, pe_01.other_pn_end)
        print(pe_02 == pe_01.other_pn_end)
        print('eq = ', pe_03 == pe_01)
        print('in = ', pe_03 in {pe_01})
        print({pe_02, pe_01.other_pn_end})
        print(pe_02 is pe_01.other_pn_end)
        print('eq 2 = ', pe_03 == pn_01.end_nd)

    if test == 'test_4':
        pg_00 = BasePolarGraph()
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
        print('pn_01 next all nd ', pn_01.next_direction_nodes())
        print('pn_01 next all pu ', pn_01.next_direction_nodes(End('pu')))
        print('pn_01 next active nd ', pn_01.next_active_direction_node())
        print('pn_01 next active pu ', pn_01.next_active_direction_node(End('pu')))

    if test == 'test_5':
        pg_00 = BasePolarGraph()
        print('pg.inf_node_pu ', pg_00.inf_node_pu)
        print('pg.inf_node_nd ', pg_00.inf_node_nd)
        pn_01 = pg_00.insert_node()  # make_nd_stable=True
        # pn_00 = copy(pn_01)
        pg_00.connect_nodes(pn_01.end_nd, pg_00.inf_node_pu.end_nd)
        print('pn_01 ', pn_01)
        print('pg nodes ', pg_00.nodes)
        print('pg links len ', len(pg_00.links))
        print('pg links ', pg_00.links)
        print('pn_01 next all nd ', pn_01.next_direction_nodes())
        print('pn_01 next all pu ', pn_01.next_direction_nodes(End('pu')))
        print('pn_01 next active nd ', pn_01.next_active_direction_node())
        print('pn_01 next active pu ', pn_01.next_active_direction_node(End('pu')))

    if test == 'test_6':
        pg_00 = BasePolarGraph()
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
        print('pn_01 next all nd ', pn_01.next_direction_nodes())
        print('pn_01 next all pu ', pn_01.next_direction_nodes(End('pu')))
        print('pn_01 next active nd ', pn_01.next_active_direction_node())
        print('pn_01 next active pu ', pn_01.next_active_direction_node(End('pu')))

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
        # print('pg_10 nodes ', pg_10.nodes[0] is pg_00.nodes[0])
