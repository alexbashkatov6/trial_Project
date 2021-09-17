from __future__ import annotations
from copy import copy, deepcopy
from collections.abc import Iterable

from nv_typing import *
from nv_names_control import names_control
from nv_string_set_class import StringSet


class PGContentDescriptor:

    def __get__(self, instance, owner=None) -> Union[PGContentDescriptor, dict]:
        if instance is None:
            return self
        if not hasattr(instance, '_content'):
            instance._content = {'whole': None}
            return instance._content
        return instance._content

    def __set__(self, instance, value):
        if not hasattr(instance, '_content'):
            instance._content = {}
        instance._content['whole'] = value


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


class PGNodeInterface:

    @strictly_typed
    def __init__(self, pn: PolarNode, end: End) -> None:
        self._pn = pn
        self._end = end
        self._move_by_link: dict[PGLink, PGMove] = dict()

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.pn, self.end)

    @strictly_typed
    def __eq__(self, other: PGNodeInterface) -> bool:
        return (self.end == other.end) and (self.pn is other.pn)

    def __hash__(self):
        return hash((self.pn, self.end))

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
    def links(self) -> set[PGLink]:
        return set(self._move_by_link.keys())

    @property
    @strictly_typed
    def moves(self) -> set[PGMove]:
        return set(self._move_by_link.values())

    @strictly_typed
    def get_move(self, link: PGLink) -> PGMove:
        return self._move_by_link[link]

    @strictly_typed
    def add_link(self, link: PGLink) -> None:
        assert not (link in self._move_by_link), 'Link already connected'
        self._move_by_link[link] = PGMove(self, link)
        self._random_move_activate()

    @strictly_typed
    def remove_link(self, link: PGLink) -> None:
        self._move_by_link.pop(link)
        self._random_move_activate()

    @property
    @strictly_typed
    def is_empty(self) -> bool:
        return len(self._move_by_link) == 0

    @property
    @strictly_typed
    def active_move(self) -> Optional[PGMove]:
        active_moves = set(filter(lambda item: item.active, self.moves))
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

    def _deactivate_all_moves(self):
        for move in self.moves:
            move.active = False

    def _random_move_activate(self):
        self._deactivate_all_moves()
        if self.moves:
            move_random = self.moves.pop()
            move_random.active = True

    @property
    @strictly_typed
    def next_active_ni(self) -> PGNodeInterface:
        active_move = self.active_move
        return active_move.link.opposite_ni(self)

    @property
    @strictly_typed
    def next_ni_s(self) -> set[PGNodeInterface]:
        return {link.opposite_ni(self) for link in self.links}


class PGMove:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self, ni: PGNodeInterface, link: PGLink) -> None:
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
    def ni(self) -> PGNodeInterface:
        return self._ni

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
    def __init__(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface, first_link_is_stable: bool = False) -> None:
        self.ni_s = (ni_1, ni_2)
        self._links = set()
        self.init_link(ni_1, ni_2, first_link_is_stable)

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.ni_s[0], self.ni_s[1])

    @property
    @strictly_typed
    def ni_s(self) -> tuple[PGNodeInterface, PGNodeInterface]:
        return self._ni_s

    @ni_s.setter
    @strictly_typed
    def ni_s(self, value: tuple[PGNodeInterface, PGNodeInterface]) -> None:
        assert value[0].pn != value[1].pn, 'Cannot connect node to itself'
        self._ni_s = value

    @strictly_typed
    def other_end(self, given_ni: PGNodeInterface) -> PGNodeInterface:
        assert given_ni in self.ni_s, 'End of node not found in ni_s'
        return (set(self.ni_s) - {given_ni}).pop()

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
        if self.links:
            if arbitrary_stable:
                return self.links.pop()
            elif stable:
                return self.stable_link
            else:
                unstable_links = self.unstable_links
                if unstable_links:
                    return unstable_links.pop()

    @strictly_typed
    def init_link(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface, init_stable: bool = False) -> PGLink:
        assert not (self.stable_link and init_stable), 'Only 1 stable link may be between same nodes'
        new_link = PGLink(ni_1, ni_2, init_stable)
        self._links.add(new_link)
        return new_link

    @strictly_typed
    def remove_link(self, link: PGLink) -> None:
        self._links.remove(link)

    @property
    @strictly_typed
    def count_of_links(self) -> int:
        return len(self.links)

    @property
    @strictly_typed
    def is_thin(self) -> bool:
        return self.count_of_links == 1


class PGLink:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface, is_stable: bool = False) -> None:
        self.stable = is_stable
        self.ni_s = (ni_1, ni_2)

    def __repr__(self):
        stable_str = 'stable' if self.stable else ''
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.ni_s[0], self.ni_s[1], stable_str)

    @property
    @strictly_typed
    def ni_s(self) -> tuple[PGNodeInterface, PGNodeInterface]:
        return self._ni_s

    @ni_s.setter
    @strictly_typed
    def ni_s(self, value: tuple[PGNodeInterface, PGNodeInterface]) -> None:
        assert value[0].pn != value[1].pn, 'Cannot connect node to itself'
        self._ni_s = value

    @property
    @strictly_typed
    def stable(self) -> bool:
        return self._stable

    @stable.setter
    @strictly_typed
    def stable(self, is_stable: bool) -> None:
        self._stable = is_stable

    @strictly_typed
    def opposite_ni(self, given_ni: PGNodeInterface) -> PGNodeInterface:
        assert given_ni in self.ni_s, 'Current end not found'
        return (set(self.ni_s) - {given_ni}).pop()


@names_control
class PolarNode:
    content = PGContentDescriptor()

    @strictly_typed
    def __init__(self) -> None:
        self._ni_negative_down, self._ni_positive_up = \
            PGNodeInterface(self, End('nd')), PGNodeInterface(self, End('pu'))

    @property
    @strictly_typed
    def count_side_connected(self) -> int:
        return int(not self.ni_nd.is_empty) + int(not self.ni_pu.is_empty)

    @property
    @strictly_typed
    def ni_nd(self) -> PGNodeInterface:
        return self._ni_negative_down

    @property
    @strictly_typed
    def ni_pu(self) -> PGNodeInterface:
        return self._ni_positive_up

    @strictly_typed
    def opposite_ni(self, given_ni: PGNodeInterface) -> PGNodeInterface:
        return ({self.ni_nd, self.ni_pu} - {given_ni}).pop()


class PGGraphMovesState:

    @strictly_typed
    def __init__(self, pg: BasePolarGraph) -> None:
        self._moves: list[PGMove] = []
        self.save_state(pg)

    @strictly_typed
    def save_state(self, pg: BasePolarGraph) -> None:
        for pn in pg.nodes:
            ni_nd, ni_pu = pn.ni_nd, pn.ni_pu
            nd_active_move, pu_active_move = ni_nd.active_move, ni_pu.active_move
            if nd_active_move:
                self._moves.append(ni_nd.active_move)
            if pu_active_move:
                self._moves.append(ni_pu.active_move)

    @strictly_typed
    def reset_state(self) -> None:
        for move in self._moves:
            move.ni.choice_move_activate(move)


class LMNSequence:
    @strictly_typed
    def __init__(self, seq: list = None) -> None:
        if not seq:
            seq = []
        self.sequence = seq

    @property
    @strictly_typed
    def sequence(self) -> list:
        return self._sequence

    @sequence.setter
    @strictly_typed
    def sequence(self, value: list) -> None:
        if value:
            self.check_sequence(value)
        self._sequence = value

    @property
    @strictly_typed
    def nodes(self) -> list[PolarNode]:
        return self.decompose()[0]

    @property
    @strictly_typed
    def links(self) -> list[PGLink]:
        return self.decompose()[1]

    @property
    @strictly_typed
    def moves(self) -> list[PGMove]:
        return self.decompose()[2]

    @staticmethod
    @strictly_typed
    def check_sequence(seq: list) -> None:
        assert len(seq) % 4 == 1, 'Len of list is not (4n+1)'
        for index, element in enumerate(seq):
            if index % 4 == 0:
                assert isinstance(element, PolarNode)
            elif index % 4 == 2:
                assert isinstance(element, PGLink)
            else:
                assert isinstance(element, PGMove)

    @strictly_typed
    def compose(self, nodes: list[PolarNode], links: list[PGLink], moves: list[PGMove]) -> None:
        nodes_r = list(reversed(nodes))
        links_r = list(reversed(links))
        moves_r = list(reversed(moves))
        sum_len = len(nodes) + len(links) + len(moves)
        for index in range(sum_len):
            if index % 4 == 0:
                self._sequence.append(nodes_r.pop())
            elif index % 4 == 2:
                self._sequence.append(links_r.pop())
            else:
                self._sequence.append(moves_r.pop())

    @strictly_typed
    def decompose(self) -> tuple[list[PolarNode], list[PGLink], list[PGMove]]:
        nodes = []
        links = []
        moves = []
        seq_r = list(reversed(self._sequence))
        for index in range(len(self._sequence)):
            if index % 4 == 0:
                nodes.append(seq_r.pop())
            elif index % 4 == 2:
                links.append(seq_r.pop())
            else:
                moves.append(seq_r.pop())
        return nodes, links, moves


class PGRoute:
    @strictly_typed
    def __init__(self, pg: PolarGraph) -> None:
        self._pg = pg
        self._route_begin = None
        self._route_end = None
        self._lmn_sequence = LMNSequence()

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.lmn.nodes)

    @property
    @strictly_typed
    def route_begin(self) -> PGNodeInterface:
        return self._route_begin

    @route_begin.setter
    @strictly_typed
    def route_begin(self, value: PGNodeInterface) -> None:
        self._route_begin = value

    @property
    @strictly_typed
    def route_end(self) -> PGNodeInterface:
        return self._route_end

    @route_end.setter
    @strictly_typed
    def route_end(self, value: PGNodeInterface) -> None:
        self._route_end = value

    @property
    @strictly_typed
    def lmn(self) -> LMNSequence:
        return self._lmn_sequence


@names_control
class PolarGraph:

    def __init__(self, bpg: BasePolarGraph = None):
        if not bpg:
            assert self.__class__ == BasePolarGraph, 'Base graph should be specified'
            bpg = self
        self._base_polar_graph = bpg
        self._nodes = set()
        self._border_ni_s = set()
        self._links = set()

    @strictly_typed
    def _init_node(self) -> PolarNode:
        node = PolarNode()
        self._nodes.add(node)
        return node

    @property
    @strictly_typed
    def base_polar_graph(self) -> BasePolarGraph:
        return self._base_polar_graph

    @property
    @strictly_typed
    def nodes(self) -> set[PolarNode]:
        return copy(self._nodes)

    @nodes.setter
    @strictly_typed
    def nodes(self, value: Iterable[PolarNode]) -> None:
        self._nodes = set(value)

    @property
    @strictly_typed
    def border_nodes(self) -> set[PolarNode]:
        return set([ni.pn for ni in self._border_ni_s])

    @property
    @strictly_typed
    def border_ni_s(self) -> set[PGNodeInterface]:
        return copy(self._border_ni_s)

    @border_ni_s.setter
    @strictly_typed
    def border_ni_s(self, value: Iterable[PGNodeInterface]) -> None:
        self._border_ni_s = set(value)

    @property
    @strictly_typed
    def links(self) -> set[PGLink]:
        return copy(self._links)

    @links.setter
    @strictly_typed
    def links(self, value: Iterable[PGLink]) -> None:
        self._links = set(value)

    @strictly_typed
    def _get_link_by_ends(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface) -> Optional[PGLink]:
        links = [link for link in self.links if {ni_1, ni_2} == set(link.ni_s)]
        assert len(links) <= 1, '2 link_groups with equal nodes and ends was found'
        if links:
            return links[0]

    @strictly_typed
    def moves_activate_by_ends(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface, pn_only_for: PolarNode = None) \
            -> None:
        link: PGLink = self._get_link_by_ends(ni_1, ni_2)
        if link:
            for ni in link.ni_s:
                if pn_only_for and not (ni.pn is pn_only_for):
                    continue
                move = ni.get_move(link)
                ni.choice_move_activate(move)

    @strictly_typed
    def get_ni_links(self, ni: PGNodeInterface) -> set[PGLink]:
        return set(link for link in self.links if (ni in link.ni_s))

    @strictly_typed
    def walk_to_borders(self, start_ni_of_node: PGNodeInterface,
                        additional_border_nodes: Optional[Iterable[PolarNode]] = None,
                        cycles_assertion: bool = True, blind_nodes_assertion: bool = True) -> set[PGRoute]:
        self.base_polar_graph.check_thin_link_groups()
        assert start_ni_of_node.pn in self.nodes, 'Begin node for find coverage not found'
        common_border_nodes = self.border_nodes
        if additional_border_nodes:
            assert all([ab_pn in self.nodes for ab_pn in additional_border_nodes]), 'Border node not found'
            common_border_nodes |= set(additional_border_nodes)
        found_nodes = {start_ni_of_node.pn}
        found_links = set()
        found_border_ni_s = {start_ni_of_node}

        found_routes = set()

        out_ni_stack = [start_ni_of_node]
        links_need_to_check: dict[PGNodeInterface, set[PGLink]] = {}
        links_stack = []
        moves_stack = []

        while out_ni_stack:
            current_out_ni = out_ni_stack[-1]
            if current_out_ni not in links_need_to_check:
                links_need_to_check[current_out_ni] = self.get_ni_links(current_out_ni)
            if not links_need_to_check[current_out_ni]:
                links_need_to_check.pop(current_out_ni)
                out_ni_stack.pop()
                if links_stack:
                    links_stack.pop()
                    moves_stack.pop()
                    moves_stack.pop()
            else:
                link_to_check = links_need_to_check[current_out_ni].pop()
                enter_ni: PGNodeInterface = link_to_check.opposite_ni(current_out_ni)
                new_node = enter_ni.pn
                out_move = current_out_ni.get_move(link_to_check)
                in_move = enter_ni.get_move(link_to_check)
                found_nodes.add(new_node)
                found_links.add(link_to_check)
                if new_node in common_border_nodes:
                    found_border_ni_s.add(enter_ni)
                    route = PGRoute(self)
                    route_nodes = [out_ni.pn for out_ni in out_ni_stack] + [enter_ni.pn]
                    route_links = copy(links_stack + [link_to_check])
                    route_moves = copy(moves_stack + [out_move, in_move])
                    route_border_ends = [start_ni_of_node, enter_ni]
                    route.lmn.compose(route_nodes, route_links, route_moves)
                    route.route_begin, route.route_end = route_border_ends
                    found_routes.add(route)
                    continue
                if cycles_assertion:
                    assert not (new_node in [out_ni.pn for out_ni in out_ni_stack]), \
                        'Loop was found: again in {}'.format(new_node)
                if blind_nodes_assertion:
                    assert new_node.count_side_connected == 2, 'Blind node was found: {}'.format(new_node)
                out_ni_stack.append(enter_ni.pn.opposite_ni(enter_ni))
                links_stack.append(link_to_check)
                moves_stack.append(out_move)
                moves_stack.append(in_move)
        return found_routes

    @strictly_typed
    def find_node_coverage(self, start_ni_of_node: PGNodeInterface,
                           additional_border_nodes: Optional[Iterable[PolarNode]] = None,
                           cycles_assertion: bool = True, blind_nodes_assertion: bool = True) -> PolarGraph:
        nodes_cov = set()
        links_cov = set()
        border_ni_s_cov = set()
        routes: set[PGRoute] = self.walk_to_borders(start_ni_of_node, additional_border_nodes, cycles_assertion,
                                                    blind_nodes_assertion)
        for route in routes:
            nodes_cov |= set(route.lmn.nodes)
            links_cov |= set(route.lmn.links)
            border_ni_s_cov |= {route.route_begin, route.route_end}

        coverage_graph = PolarGraph(self.base_polar_graph)
        coverage_graph.nodes = nodes_cov
        coverage_graph.links = links_cov
        coverage_graph.border_ni_s = border_ni_s_cov
        return coverage_graph

    @strictly_typed
    def cut_subgraph(self, border_nodes: Iterable[PolarNode]) -> PolarGraph:
        sbg_ni_s: set[PGNodeInterface] = set()
        sbg_links = self.links
        sbg_nodes = set()
        for border_ni in self.border_ni_s:
            local_coverage: PolarGraph = self.find_node_coverage(border_ni, border_nodes)
            sbg_links -= local_coverage.links
        assert sbg_links, 'Empty subgraph was found'
        for link in sbg_links:
            sbg_ni_s |= set(link.ni_s)
            sbg_nodes |= set(ni.pn for ni in link.ni_s)
        subgraph = PolarGraph(self.base_polar_graph)
        subgraph.nodes = sbg_nodes
        subgraph.links = sbg_links
        subgraph.border_ni_s = sbg_ni_s - set(ni.pn.opposite_ni(ni) for ni in sbg_ni_s)
        return subgraph

    @strictly_typed
    def find_routes(self, start_node: PolarNode, end_node: PolarNode) -> set[PGRoute]:
        found_route_candidates: set[PGRoute] = set()
        for start_ni in (start_node.ni_nd,  start_node.ni_pu):
            found_route_candidates |= self.walk_to_borders(start_ni, [end_node])
        return set(frc for frc in found_route_candidates if frc.route_end.pn is end_node)

    @strictly_typed
    def find_single_route(self, start_node: PolarNode, end_node: PolarNode,
                          checkpoint_nodes: Iterable[PolarNode] = None) -> PGRoute:
        if not checkpoint_nodes:
            checkpoint_nodes = set()
        candidate_routes: set[PGRoute] = self.find_routes(start_node, end_node)
        assert candidate_routes, 'Routes from {} to {} not found'.format(start_node, end_node)
        routes_throw_checkpoints = set()
        for candidate_route in candidate_routes:
            if set(checkpoint_nodes) <= set(candidate_route.lmn.nodes):
                routes_throw_checkpoints.add(candidate_route)
        assert routes_throw_checkpoints, 'Route throw checkpoint nodes not found'
        assert len(routes_throw_checkpoints) == 1, 'More then 1 route throw checkpoint nodes not found'
        return routes_throw_checkpoints.pop()

    @strictly_typed
    def activate_route(self, route: PGRoute) -> None:
        for link in route.lmn.links:
            self.moves_activate_by_ends(*link.ni_s)


@names_control
class BasePolarGraph(PolarGraph):

    def __init__(self):
        super().__init__()

        self._infinity_node_positive_up = self._init_node()
        self._infinity_node_negative_down = self._init_node()
        self.border_ni_s = {self.inf_node_pu.ni_nd, self.inf_node_nd.ni_pu}

        self._link_groups = set()

    @property
    @strictly_typed
    def inf_node_pu(self) -> PolarNode:
        return self._infinity_node_positive_up

    @property
    @strictly_typed
    def inf_node_nd(self) -> PolarNode:
        return self._infinity_node_negative_down

    @property
    @strictly_typed
    def link_groups(self) -> set[PGLinkGroup]:
        return copy(self._link_groups)

    @strictly_typed
    def check_thin_link_groups(self) -> None:
        assert all([link_group.is_thin for link_group in self.link_groups]), 'Base graph link_groups is not thin'

    @strictly_typed
    def connect_nodes(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface, link_is_stable: bool = False) -> PGLink:
        assert not (ni_1.pn is ni_2.pn), 'Cannot connect node {} to himself'.format(ni_1.pn)
        assert {ni_1.pn, ni_2.pn} <= set(self.nodes), \
            'Nodes {}, {} not found in graph'.format(ni_1.pn, ni_2.pn)
        existing_link_group = self._get_link_group_by_ends(ni_1, ni_2)
        if existing_link_group:
            new_link = existing_link_group.init_link(link_is_stable)
        else:
            new_link_group = self._init_new_link_group(ni_1, ni_2, link_is_stable)
            new_link = new_link_group.get_link()
        ni_1.add_link(new_link)
        ni_2.add_link(new_link)
        self._refresh_link_groups_and_links()
        return new_link

    @strictly_typed
    def _disconnect_nodes(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface) -> None:
        link_group = self._get_link_group_by_ends(ni_1, ni_2)
        unstable_links = link_group.unstable_links
        if not unstable_links:
            return
        else:
            link = unstable_links.pop()
        ni_1.remove_link(link)
        ni_2.remove_link(link)
        link_group.remove_link(link)
        self._refresh_link_groups_and_links()

    @strictly_typed
    def insert_node(self, ni_of_positive_up_node: PGNodeInterface,
                    ni_of_negative_down_node: PGNodeInterface,
                    insertion_node: PolarNode = None,
                    make_pu_stable: bool = False, make_nd_stable: bool = False) -> PolarNode:
        if not insertion_node:
            insertion_node = self._init_node()
        existing_old_nodes_link_group = self._get_link_group_by_ends(ni_of_positive_up_node, ni_of_negative_down_node)
        if existing_old_nodes_link_group:
            self._disconnect_nodes(ni_of_positive_up_node, ni_of_negative_down_node)
        self.connect_nodes(ni_of_positive_up_node, insertion_node.ni_pu, make_pu_stable)
        self.connect_nodes(ni_of_negative_down_node, insertion_node.ni_nd, make_nd_stable)
        return insertion_node

    def _refresh_link_groups_and_links(self):
        self._links.clear()
        for link_group in self.link_groups:
            if link_group.count_of_links == 0:
                self._link_groups.remove(link_group)
            else:
                self._links |= link_group.links

    @strictly_typed
    def _get_link_group_by_ends(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface) -> Optional[PGLinkGroup]:
        link_groups = [link_group for link_group in self.link_groups
                       if {ni_1, ni_2} == set(link_group.ni_s)]
        assert len(link_groups) <= 1, '2 link_groups with equal nodes and ends was found'
        if link_groups:
            return link_groups[0]

    @strictly_typed
    def _check_new_link_group_existing_possibility(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface) -> bool:
        return not bool(self._get_link_group_by_ends(ni_1, ni_2))

    @strictly_typed
    def _init_new_link_group(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface,
                             first_link_is_stable: bool = False) -> PGLinkGroup:
        assert self._check_new_link_group_existing_possibility(ni_1, ni_2), 'Link_group already exists'
        new_link_group = PGLinkGroup(ni_1, ni_2, first_link_is_stable)
        self._link_groups.add(new_link_group)
        return new_link_group

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

        def create_graph_1():
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu,
                                    make_pu_stable=True, make_nd_stable=True)
            pn_2 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_3 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_4 = pg_0.insert_node(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_5 = pg_0.insert_node(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            # pg_0.check_thin_link_groups()
            nodes.extend([pn_1, pn_2, pn_3, pn_4, pn_5])
            return pg_0, nodes


        def create_graph_2():
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_2 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_3 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_4 = pg_0.insert_node(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_5 = pg_0.insert_node(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            # pg_0.check_thin_link_groups()
            nodes.extend([pn_1, pn_2, pn_3, pn_4, pn_5])
            return pg_0, nodes


        def create_graph_3():
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_pu.ni_nd)
            # pg_0.check_thin_link_groups()
            nodes.extend([pn_1])
            return pg_0, nodes


        def create_graph_4():
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_2 = pg_0.insert_node(pn_1.ni_nd, pn_1.ni_pu)
            pn_3 = pg_0.insert_node(pn_1.ni_nd, pn_2.ni_pu)
            # pg_0.check_thin_link_groups()
            nodes.extend([pn_1, pn_2, pn_3])
            return pg_0, nodes


        def create_graph_5() -> tuple[PolarGraph, list[PolarNode]]:
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu, make_nd_stable=True)
            pn_2 = pg_0.insert_node(pg_0.inf_node_nd.ni_pu, pn_1.ni_nd)
            pg_0.connect_nodes(pg_0.inf_node_nd.ni_pu, pn_2.ni_nd)
            pn_3 = pg_0.insert_node(pg_0.inf_node_pu.ni_nd, pn_2.ni_pu)
            # pg_0.check_thin_link_groups()
            nodes.extend([pn_1, pn_2, pn_3])
            return pg_0, nodes


        pg_00, nodes_00 = create_graph_2()

        # routes_ = pg_00.walk_to_borders(pg_00.inf_node_pu.ni_nd)
        # cover_graph: PolarGraph = pg_00.find_node_coverage(nodes_00[1].ni_pu, [nodes_00[2], nodes_00[3]])
        # subgraph_: PolarGraph = pg_00.cut_subgraph([nodes_00[2], nodes_00[3], nodes_00[4], nodes_00[5]])
        # routes_pn1_pn2_: set[PGRoute] = pg_00.find_routes(pg_00.inf_node_pu, nodes_00[1])

        route_from_to_: PGRoute = pg_00.find_single_route(pg_00.inf_node_pu, pg_00.inf_node_nd,
                                                          [nodes_00[2], nodes_00[4]])
        pg_00.activate_route(route_from_to_)

        for node_ in route_from_to_.lmn.nodes:
            node_.content = 'ups'
            node_.content['my_key'] = 'lala'
        for node_ in route_from_to_.lmn.nodes:
            print('node content = ', node_.content)

        # for move_ in route_from_to_.lmn.moves:
        #     print(move_.active)

        # print('routes_count = ', len(routes_))
        # for route_ in routes_:
        #     print(route_)
        #
        # print('cover_graph = ', cover_graph)
        # print('cover_graph nodes = ', len(cover_graph.nodes), cover_graph.nodes)
        # print('cover_graph links = ', len(cover_graph.links), cover_graph.links)
        # print('cover_graph borders = ', len(cover_graph.border_ni_s), cover_graph.border_ni_s)
        #
        # print('sub_graph = ', subgraph_)
        # print('sub_graph nodes = ', len(subgraph_.nodes), subgraph_.nodes)
        # print('sub_graph links = ', len(subgraph_.links), subgraph_.links)
        # print('sub_graph borders = ', len(subgraph_.border_ni_s), subgraph_.border_ni_s)

        # print('routes_pn1_pn2_count = ', len(routes_pn1_pn2_))
        # for route_pn1_pn2_ in routes_pn1_pn2_:
        #     print(route_pn1_pn2_)

        # print('route_from_to_ = ', route_from_to_)

        # lmn = LMNSequence([1, 2, 3])

        # pg_00.find_node_coverage(pg_00.inf_node_nd.end_pu)

        # print('pg.inf_node_pu ', pg_00.inf_node_pu)
        # print('pg.inf_node_nd ', pg_00.inf_node_nd)
        # print('links in pg ', pg_00.links)
        # print('moves of inf_pu pu', pg_00.inf_node_pu.ni_pu.moves_group.moves)
        # print('moves of inf_pu nd', pg_00.inf_node_pu.ni_nd.moves_group.moves)
        # print('pn_01 ', pn_01)
        # print('pg nodes ', pg_00.nodes)
        # print('pg.inf_node_pu ', pg_00.inf_node_pu)
        # print('pg.inf_node_nd ', pg_00.inf_node_nd)
        # print('links in pg ', pg_00.links)
        # print('len of links in pg ', len(pg_00.links))
        # print('moves of inf_pu pu', pg_00.inf_node_pu.ni_pu.moves_group.moves)
        # print('moves of inf_pu nd', pg_00.inf_node_pu.ni_nd.moves_group.moves)
        # print('active move of inf_pu pu', pg_00.inf_node_pu.ni_pu.moves_group.active_move)
        # print('active move of inf_pu nd', pg_00.inf_node_pu.ni_nd.moves_group.active_move)
        # print('next nodes of inf_pu pu', pg_00.inf_node_pu.ni_pu.next_nodes)
        # print('next nodes of inf_pu nd', pg_00.inf_node_pu.ni_nd.next_nodes)
        # print('Before activation')
        # ms = PGGraphMovesState(pg_00)
        # # print('active node of inf_pu pu', pg_00.inf_node_pu.ni_pu.next_active_node)
        # print('active node of inf_pu nd', pg_00.inf_node_pu.ni_nd.next_active_node)
        # print('active node of pn_01 pu', pn_01.ni_pu.next_active_node)
        # pg_00.moves_activate_by_ends(pn_01.end_pu, pg_00.inf_node_pu.end_nd)
        # print('After activation')
        # # print('active node of inf_pu pu', pg_00.inf_node_pu.ni_pu.next_active_node)
        # print('active node of inf_pu nd', pg_00.inf_node_pu.ni_nd.next_active_node)
        # print('active node of pn_01 pu', pn_01.ni_pu.next_active_node)
        # print('After reset')
        # ms.reset_state()
        # # print('active node of inf_pu pu', pg_00.inf_node_pu.ni_pu.next_active_node)
        # print('active node of inf_pu nd', pg_00.inf_node_pu.ni_nd.next_active_node)
        # print('active node of pn_01 pu', pn_01.ni_pu.next_active_node)

    if test == 'test_3':
        pass
        # pn_01 = PolarNode()
        # print(End('nd') == 'pu')
        # pe_01 = PNEnd(pn_01, End('nd'))
        # pe_02 = PNEnd(pn_01, End('pu'))
        # pe_03 = PNEnd(pn_01, End('nd'))
        # print(pe_01, pe_01.other_pn_end)
        # print(pe_02 == pe_01.other_pn_end)
        # print('eq = ', pe_03 == pe_01)
        # print('in = ', pe_03 in {pe_01})
        # print({pe_02, pe_01.other_pn_end})
        # print(pe_02 is pe_01.other_pn_end)
        # print('eq 2 = ', pe_03 == pn_01.end_nd)

    if test == 'test_4':
        pg_00 = BasePolarGraph()
        print('pg.inf_node_pu ', pg_00.inf_node_pu)
        print('pg.inf_node_nd ', pg_00.inf_node_nd)
        pn_01 = pg_00.insert_node()  # make_nd_stable=True
        # pn_00 = copy(pn_01)
        pn_02 = pg_00.insert_node(ni_of_negative_down_node=pn_01.end_pu, make_nd_stable=True)
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
        pn_02 = pg_00.insert_node(ni_of_negative_down_node=pn_01.end_pu, make_nd_stable=True)
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
