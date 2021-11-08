from __future__ import annotations
from copy import copy, deepcopy
from collections import OrderedDict
from itertools import combinations
from functools import partial
import time

from nv_typing import *
from nv_bounded_string_set_class import bounded_string_set
from nv_associations import NodeAssociation, LinkAssociation, MoveAssociation
from nv_cell import Cell, CellChecker, AutoValueSetter
from nv_errors import CycleError
# import nv_cell

# if __name__ == '__main__':
#     import re
#
#     class GlobalNamesManager:
#         def __init__(self):
#             self._name_to_obj: dict[str, Any] = {}
#             self._obj_to_name: dict[Any, str] = {}  # for check obj repeating
#
#         def register_obj_name(self, obj, name):
#             if type(obj) == str:
#                 obj, name = name, obj
#             assert name not in self.name_to_obj, 'Name repeating'
#             assert obj not in self.obj_to_name, 'Obj repeating'
#             assert not (obj is None), 'None str_value cannot be registered'
#             self._name_to_obj[name] = obj
#             self._obj_to_name[obj] = name
#
#         def remove_obj_name(self, obj_or_name):
#             obj, name = (self.name_to_obj[obj_or_name], obj_or_name) if type(obj_or_name) == str \
#                 else (obj_or_name, self.obj_to_name[obj_or_name])
#             self._name_to_obj.pop(name)
#             self._obj_to_name.pop(obj)
#
#         def rename_obj(self, obj, new_name):
#             self.remove_obj_name(obj)
#             self.register_obj_name(obj, new_name)
#
#         def check_new_name(self, name):
#             return not (name in self.name_to_obj)
#
#         @property
#         def name_to_obj(self) -> dict[str, Any]:
#             return copy(self._name_to_obj)
#
#         @property
#         def obj_to_name(self) -> dict[Any, str]:
#             return copy(self._obj_to_name)
#
#
#     GNM = GlobalNamesManager()
#
#     class NameDescriptor:
#
#         def __init__(self, start_index=1):
#             assert type(start_index) == int, 'Start index must be int'
#             self.start_index = start_index
#
#         def __get__(self, instance, owner=None):
#
#             if not (instance is None) and not hasattr(instance, '_name'):
#                 instance._name = None
#
#             if instance is None:
#                 return owner.__name__
#             else:
#                 if not (instance._name is None):
#                     return instance._name
#                 else:
#                     raise ValueError('Name is not defined')
#
#         def __set__(self, instance, name_candidate):
#             if hasattr(instance, '_name'):
#                 GNM.remove_obj_name(instance)
#             prefix = instance.__class__.__name__ + '_'
#             if name_candidate == 'auto_name':
#                 i = self.start_index
#                 while True:
#                     if i < 1:
#                         name_candidate = '{}{}'.format(prefix, '0' * (1 - i))
#                     else:
#                         name_candidate = '{}{}'.format(prefix, i)
#                     if GNM.check_new_name(name_candidate):
#                         break
#                     else:
#                         i += 1
#             else:
#                 assert type(name_candidate) == str, 'Name need be str'
#                 assert bool(re.fullmatch(r'\w+', name_candidate)), 'Name have to consists of alphas, nums and _'
#                 assert name_candidate.startswith(prefix), 'Name have to begin from className_'
#                 assert name_candidate != prefix, 'name cannot be == prefix; add specification to end'
#                 assert not name_candidate[
#                            len(prefix):].isdigit(), 'Not auto-name cannot be (prefix + int); choose other name'
#                 assert GNM.check_new_name(name_candidate), 'Name {} already exists'.format(name_candidate)
#             instance._name = name_candidate
#             GNM.register_obj_name(instance, name_candidate)

    # PolarNode.name = NameDescriptor(-1)
    # PolarNode.__repr__ = lambda x: x.name
    # setattr(BasePolarGraph, 'name', NameDescriptor(-1))
    # BasePolarGraph.name = NameDescriptor(-1)
    # bpg = BasePolarGraph()
    # print(bpg.name)
    # BasePolarGraph.__repr__ = lambda x: x.name

End = bounded_string_set('End', [['negative_down', 'nd'], ['positive_up', 'pu']])


class PGNodeInterface:

    @strictly_typed
    def __init__(self, pn: PolarNode, end: End) -> None:
        self._pn = pn
        self._end = end
        self._move_by_link: OrderedDict[PGLink, PGMove] = OrderedDict()

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.pn, self.end)

    @property
    @strictly_typed
    def base_polar_graph(self) -> BasePolarGraph:
        return self.pn.base_polar_graph

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
    def ordered_moves(self) -> list[PGMove]:
        return list(self._move_by_link.values())

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


class PGMove:

    @strictly_typed
    def __init__(self, ni: PGNodeInterface, link: PGLink) -> None:
        self._link = link
        self._ni = ni
        self._active = False

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.ni, self.link)

    @property
    @strictly_typed
    def base_polar_graph(self) -> BasePolarGraph:
        return self.ni.base_polar_graph

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
    def __init__(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface,
                 first_link_is_stable: bool = False) -> None:
        self.ni_s = (ni_1, ni_2)
        self._links = set()
        self.init_link(first_link_is_stable)

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.ni_s[0], self.ni_s[1])

    @property
    @strictly_typed
    def base_polar_graph(self) -> BasePolarGraph:
        return self.ni_s[0].base_polar_graph

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
    def init_link(self, init_stable: bool = False) -> PGLink:
        assert not (self.stable_link and init_stable), 'Only 1 stable link may be between same nodes'
        new_link = PGLink(*self.ni_s, init_stable)
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

    @strictly_typed
    def __init__(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface,
                 is_stable: bool = False) -> None:
        self.ni_s = (ni_1, ni_2)
        self.stable = is_stable

    def __repr__(self):
        stable_str = 'stable' if self.stable else ''
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.ni_s[0], self.ni_s[1], stable_str)

    @property
    @strictly_typed
    def base_polar_graph(self) -> BasePolarGraph:
        return self.ni_s[0].base_polar_graph

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


class PolarNode:
    # name = NameDescriptor(-1) if __name__ == '__main__' else ''
    # __repr__ = (lambda x: x.name) if __name__ == '__main__' else object.__repr__
    #     return self.name

    @strictly_typed
    def __init__(self, bpg: BasePolarGraph) -> None:
        # self.name = 'auto_name'
        self._base_polar_graph = bpg
        self._ni_negative_down, self._ni_positive_up = \
            PGNodeInterface(self, End('nd')), \
            PGNodeInterface(self, End('pu'))

    @property
    @strictly_typed
    def base_polar_graph(self) -> BasePolarGraph:
        return self._base_polar_graph

    @base_polar_graph.setter
    @strictly_typed
    def base_polar_graph(self, val: BasePolarGraph) -> None:
        self._base_polar_graph = val

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


class PolarGraph:
    # name = NameDescriptor() if __name__ == '__main__' else ''
    # __repr__ = (lambda x: x.name) if __name__ == '__main__' else object.__repr__
    # name = NameDescriptor() if __name__ == '__main__' else object.__repr__  # NameDescriptor()

    def __init__(self, bpg: Optional[BasePolarGraph] = None):
        # self.name = 'auto_name'
        if not bpg:
            assert self.__class__ == BasePolarGraph, 'Base graph should be specified'
            bpg = self
        self._base_polar_graph = bpg
        self._nodes = set()
        self._border_ni_s = set()
        self._links = set()
        self._moves = set()

    # def __repr__(self):
    #     return self.name

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
    def inf_nodes(self) -> set[PolarNode]:
        return {self.base_polar_graph.inf_node_pu, self.base_polar_graph.inf_node_nd}

    @property
    @strictly_typed
    def not_inf_nodes(self) -> set[PolarNode]:
        return self.nodes - {self.base_polar_graph.inf_node_pu, self.base_polar_graph.inf_node_nd}

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

    @property
    @strictly_typed
    def moves(self) -> set[PGMove]:
        return copy(self._moves)

    @moves.setter
    @strictly_typed
    def moves(self, value: Iterable[PGMove]) -> None:
        self._moves = set(value)

    @strictly_typed
    def _get_link_by_ends(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface) -> Optional[PGLink]:
        links = [link for link in self.links if {ni_1, ni_2} == set(link.ni_s)]
        assert len(links) <= 1, '2 link_groups with equal nodes and ends was found'
        if links:
            return links[0]

    @strictly_typed
    def _moves_activate_by_ends(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface, pn_only_for: PolarNode = None) \
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
                        cycles_assertion: bool = True, blind_nodes_assertion: bool = True) \
            -> tuple[set[PGRoute], list[set[PolarNode]]]:
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
        node_layers = []

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
                    route = PGRoute(self.base_polar_graph)
                    route_nodes = [out_ni.pn for out_ni in out_ni_stack] + [enter_ni.pn]
                    for layer_depth, route_node in enumerate(route_nodes):
                        if layer_depth >= len(node_layers):
                            node_layers.append(set())
                        node_layers[layer_depth].add(route_node)
                    route_links = copy(links_stack + [link_to_check])
                    route_moves = copy(moves_stack + [out_move, in_move])
                    route_border_ends = [start_ni_of_node, enter_ni]
                    route.compose(route_nodes, route_links, route_moves)
                    route.route_begin, route.route_end = route_border_ends
                    found_routes.add(route)
                    continue
                if cycles_assertion and (new_node in [out_ni.pn for out_ni in out_ni_stack]):
                    raise CycleError('Dependence loop was found')  # : again in {}.format(new_node)
                if blind_nodes_assertion:
                    assert new_node.count_side_connected == 2, 'Blind node was found: {}'.format(new_node)
                out_ni_stack.append(enter_ni.pn.opposite_ni(enter_ni))
                links_stack.append(link_to_check)
                moves_stack.append(out_move)
                moves_stack.append(in_move)
        return found_routes, node_layers

    @strictly_typed
    def find_node_coverage(self, start_ni_of_node: PGNodeInterface,
                           additional_border_nodes: Optional[Iterable[PolarNode]] = None,
                           cycles_assertion: bool = True, blind_nodes_assertion: bool = True) -> PolarGraph:
        nodes_cov = set()
        links_cov = set()
        border_ni_s_cov = set()
        routes: set[PGRoute] = self.walk_to_borders(start_ni_of_node, additional_border_nodes, cycles_assertion,
                                                    blind_nodes_assertion)[0]
        for route in routes:
            nodes_cov |= set(route.nodes)
            links_cov |= set(route.links)
            border_ni_s_cov |= {route.route_begin, route.route_end}

        coverage_graph = PolarGraph(self.base_polar_graph)
        coverage_graph.nodes = nodes_cov
        coverage_graph.links = links_cov
        coverage_graph.border_ni_s = border_ni_s_cov
        return coverage_graph

    # @strictly_typed
    # def layered_representation(self, start_ni_of_node: PGNodeInterface) -> list[set[PolarNode]]:
    #     return self.walk_to_borders(start_ni_of_node)[1]

    @strictly_typed
    def find_routes(self, start_node: PolarNode, end_node: PolarNode) -> set[PGRoute]:
        found_route_candidates: set[PGRoute] = set()
        for start_ni in (start_node.ni_nd, start_node.ni_pu):
            found_route_candidates |= self.walk_to_borders(start_ni, [end_node])[0]
        return set(frc for frc in found_route_candidates if frc.route_end.pn is end_node)

    @strictly_typed
    def find_single_route(self, start_node: PolarNode, end_node: PolarNode,
                          checkpoint_nodes: Iterable[PolarNode] = None) -> Optional[PGRoute]:
        if not checkpoint_nodes:
            checkpoint_nodes = set()
        candidate_routes: set[PGRoute] = self.find_routes(start_node, end_node)
        # not_found_assertion: bool = True
        # if not candidate_routes and not not_found_assertion:
        #     return
        assert candidate_routes, 'Routes from {} to {} not found'.format(start_node, end_node)
        routes_throw_checkpoints = set()
        for candidate_route in candidate_routes:
            if set(checkpoint_nodes) <= set(candidate_route.nodes):
                routes_throw_checkpoints.add(candidate_route)
        assert routes_throw_checkpoints, 'Route throw checkpoint nodes not found'
        assert len(routes_throw_checkpoints) == 1, 'More then 1 route throw checkpoint nodes was found'
        return routes_throw_checkpoints.pop()

    @strictly_typed
    def cut_subgraph(self, border_nodes: Iterable[PolarNode], include_common_links: bool = False) -> PolarGraph:
        # common_links = in external graph and in internal graph at the same time
        sbg_ni_s: set[PGNodeInterface] = set()
        sbg_nodes = set()
        if include_common_links:
            sbg_links = set()
            for node_pair in combinations(border_nodes, 2):
                start_node, end_node = node_pair
                candidate_routes: set[PGRoute] = self.find_routes(start_node, end_node)
                for cr in candidate_routes:
                    sbg_links |= cr.links
        else:
            sbg_links = self.links
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
    def free_roll(self, start_ni_of_node: PGNodeInterface = None, stop_nodes: Iterable[PolarNode] = None,
                  not_found_assertion: bool = True) -> PGRoute:
        if start_ni_of_node is None:
            start_ni_of_node = self.base_polar_graph.inf_node_pu.ni_nd
        if not stop_nodes:
            stop_nodes = self.border_nodes
        elif not not_found_assertion:
            stop_nodes |= self.border_nodes
        current_ni = start_ni_of_node
        found_nodes, found_links, found_moves = [], [], []
        end_ni = None
        while current_ni:
            found_nodes.append(current_ni.pn)
            out_move = current_ni.active_move
            found_moves.append(out_move)
            link = out_move.link
            found_links.append(link)
            enter_ni: PGNodeInterface = link.opposite_ni(current_ni)
            enter_move = enter_ni.get_move(link)
            found_moves.append(enter_move)
            new_node = enter_ni.pn
            if new_node in stop_nodes:
                found_nodes.append(new_node)
                end_ni = enter_ni
                break
            elif new_node in self.border_nodes:
                assert False, 'Stop node is not found'
            else:
                current_ni = new_node.opposite_ni(enter_ni)
        route = PGRoute(self.base_polar_graph)
        route.compose(found_nodes, found_links, found_moves)
        route.route_begin, route.route_end = start_ni_of_node, end_ni
        return route

    @strictly_typed
    def activate_route(self, route: PGRoute) -> None:
        for link in route.links:
            self._moves_activate_by_ends(*link.ni_s)


class PGRoute(PolarGraph):

    @strictly_typed
    def __init__(self, bpg: BasePolarGraph) -> None:
        super().__init__(bpg)
        self._route_begin = None
        self._route_end = None
        self._sequence = []
        self._ordered_nodes = None

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.ordered_nodes)

    @property
    @strictly_typed
    def sequence(self) -> list[Union[PolarNode, PGLink, PGMove]]:
        return self._sequence

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
        self._nodes, self._links, self._moves = set(nodes), set(links), set(moves)
        self._ordered_nodes = nodes

    @property
    @strictly_typed
    def ordered_nodes(self) -> list[PolarNode]:
        return self._ordered_nodes

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


class BasePolarGraph(PolarGraph):
    # name = NameDescriptor() if __name__ == '__main__' else ''
    # __repr__ = (lambda x: x.name) if __name__ == '__main__' else object.__repr__
    # name = nv_cell.NameDescriptor()

    def __init__(self):
        super().__init__()
        # self.name = 'auto_name'

        self._infinity_node_positive_up = self._init_node()
        self._infinity_node_negative_down = self._init_node()

        self._physical_links = False
        self._link_groups = set()
        self._am = AssociationsManager(self)

        self.border_ni_s = {self.inf_node_pu.ni_nd, self.inf_node_nd.ni_pu}
        self.connect_nodes(*self.border_ni_s)

    # def __repr__(self):
    #     return self.name

    @strictly_typed
    def _init_node(self) -> PolarNode:
        node = PolarNode(self)
        self._nodes.add(node)
        return node

    @property
    @strictly_typed
    def am(self) -> AssociationsManager:
        return self._am

    @am.setter
    @strictly_typed
    def am(self, value: AssociationsManager) -> None:
        self._am = value

    @property
    @strictly_typed
    def physical_links(self) -> bool:
        return self._physical_links

    @physical_links.setter
    @strictly_typed
    def physical_links(self, value: bool) -> None:
        self._physical_links = value

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

    @link_groups.setter
    @strictly_typed
    def link_groups(self, val: Iterable[PGLinkGroup]) -> None:
        self._link_groups = set(val)

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
        self._refresh_link_groups_links_moves()
        return new_link

    @strictly_typed
    def disconnect_nodes(self, ni_1: PGNodeInterface, ni_2: PGNodeInterface) -> \
            Optional[tuple[PGLink, tuple[PGMove, PGMove]]]:
        link_group = self._get_link_group_by_ends(ni_1, ni_2)
        unstable_links = link_group.unstable_links
        if not unstable_links:
            return
        else:
            link = unstable_links.pop()
        moves = ni_1.get_move(link), ni_2.get_move(link)
        ni_1.remove_link(link)
        ni_2.remove_link(link)
        link_group.remove_link(link)
        self._refresh_link_groups_links_moves()
        return link, moves

    @strictly_typed
    def insert_node_single_link(self, ni_of_positive_up_node: PGNodeInterface = None,
                                ni_of_negative_down_node: PGNodeInterface = None,
                                make_pu_stable: bool = False, make_nd_stable: bool = False) \
            -> tuple[PolarNode, PGLink, PGLink]:
        if ni_of_positive_up_node is None:
            ni_of_positive_up_node = self.inf_node_pu.ni_nd
        if ni_of_negative_down_node is None:
            ni_of_negative_down_node = self.inf_node_nd.ni_pu
        insertion_node = self._init_node()
        existing_old_nodes_link_group = self._get_link_group_by_ends(ni_of_positive_up_node, ni_of_negative_down_node)
        pu_link = self.connect_nodes(ni_of_positive_up_node, insertion_node.ni_pu, make_pu_stable)
        nd_link = self.connect_nodes(ni_of_negative_down_node, insertion_node.ni_nd, make_nd_stable)
        if existing_old_nodes_link_group:
            old_link, old_moves = self.disconnect_nodes(ni_of_positive_up_node, ni_of_negative_down_node)
            self.am.replace_link_after_split(old_link, old_moves, (pu_link, nd_link))
        return insertion_node, pu_link, nd_link

    @strictly_typed
    def insert_node_neck(self, ni_necked: PGNodeInterface, make_between_stable: bool = False) -> PolarNode:
        insertion_node: PolarNode = self._init_node()
        if ni_necked.end == 'nd':
            ni_instead_necked = insertion_node.ni_nd
        else:
            ni_instead_necked = insertion_node.ni_pu
        ni_s_for_reconnect: set[PGNodeInterface] = set()
        link_nis_before = {}
        old_moves = {}
        for link in ni_necked.links:
            assert not link.stable, 'Stable link was found when makes neck'
            ni = link.opposite_ni(ni_necked)
            ni_s_for_reconnect.add(ni)
            link_nis_before[ni], old_moves[ni] = self.disconnect_nodes(*link.ni_s)
        for ni_for_reconnect in ni_s_for_reconnect:
            link_after = self.connect_nodes(ni_instead_necked, ni_for_reconnect)
            self.am.replace_link_after_node_change(link_nis_before[ni_for_reconnect], old_moves[ni_for_reconnect],
                                                   link_after)
        self.connect_nodes(insertion_node.opposite_ni(ni_instead_necked), ni_necked, make_between_stable)
        return insertion_node

    @strictly_typed
    def aggregate(self, insert_pg: BasePolarGraph,
                  ni_for_pu_connect: PGNodeInterface = None, ni_for_nd_connect: PGNodeInterface = None) -> None:
        if (ni_for_pu_connect is None) and (ni_for_nd_connect is None):
            new_node = self.insert_node_neck(self.inf_node_nd.ni_pu)
            ni_for_pu_connect = new_node.ni_nd
            ni_for_nd_connect = self.inf_node_nd.ni_pu
        assert len(ni_for_pu_connect.links) <= 1, 'Count of links in old ni should be <=1: {}'.format(ni_for_pu_connect)
        assert len(ni_for_nd_connect.links) <= 1, 'Count of links in old ni should be <=1: {}'.format(ni_for_nd_connect)
        if len(ni_for_pu_connect.links) == 1:
            link = ni_for_pu_connect.links.pop()
            assert {ni_for_pu_connect, ni_for_nd_connect} == set(link.ni_s), 'Old ni_s should be connected between'
        old_links_pu_connection = insert_pg.inf_node_pu.ni_nd.links
        old_links_nd_connection = insert_pg.inf_node_nd.ni_pu.links
        self.disconnect_nodes(ni_for_pu_connect, ni_for_nd_connect)
        for node in insert_pg.not_inf_nodes:
            node.base_polar_graph = self
        self.nodes |= insert_pg.not_inf_nodes
        for old_link in old_links_pu_connection:
            _, move_ni_s = insert_pg.disconnect_nodes(*old_link.ni_s)
            ni = old_link.opposite_ni(insert_pg.inf_node_pu.ni_nd)
            new_link = self.connect_nodes(ni, ni_for_pu_connect)
            self.am.replace_link_after_node_change(old_link, move_ni_s, new_link, insert_pg.am)
        for old_link in old_links_nd_connection:
            _, move_ni_s = insert_pg.disconnect_nodes(*old_link.ni_s)
            ni = old_link.opposite_ni(insert_pg.inf_node_nd.ni_pu)
            new_link = self.connect_nodes(ni, ni_for_nd_connect)
            self.am.replace_link_after_node_change(old_link, move_ni_s, new_link, insert_pg.am)
        self.links |= insert_pg.links
        self.link_groups |= insert_pg.link_groups
        self.moves |= insert_pg.moves

        ins_am = insert_pg.am
        self.am.aggregate_refresh_cells(ins_am, insert_pg.not_inf_nodes | insert_pg.not_inf_nodes | insert_pg.moves)

    @strictly_typed
    def remove_nodes(self, nodes: Iterable[PolarNode]) -> None:
        nodes = set(nodes)
        if self.physical_links:
            for node in nodes:
                assert len(node.ni_nd.links) == 1 and len(node.ni_pu.links) == 1, 'For material graph can delete ' \
                                                                                  'only through nodes'
                # ! implementation of connect/disconnect and in assoc manager
        else:
            for node in nodes:
                for ni in [node.ni_nd, node.ni_pu]:
                    for link in ni.links:
                        self.disconnect_nodes(*link.ni_s)
            self.nodes -= nodes
            if not self.not_inf_nodes:
                self.connect_nodes(*self.border_ni_s)
            else:
                for node in self.not_inf_nodes:
                    if node.ni_nd.is_empty:
                        self.connect_nodes(node.ni_nd, self.inf_node_nd.ni_pu)
                    if node.ni_pu.is_empty:
                        self.connect_nodes(node.ni_pu, self.inf_node_nd.ni_nd)
            self.am.refresh_cells_unphysical_nodes_remove()

    def _refresh_link_groups_links_moves(self):
        self._links.clear()
        self._moves.clear()
        for link_group in self.link_groups:
            if link_group.count_of_links == 0:
                self._link_groups.remove(link_group)
            else:
                self._links |= link_group.links
        for link in self._links:
            link: PGLink
            for ni in link.ni_s:
                self._moves |= ni.moves

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


class AssociationsManager:

    @strictly_typed
    def __init__(self, bpg: BasePolarGraph) -> None:
        self._base_polar_graph = bpg

        self._cell_dicts = {}

        self._node_assoc_class = None
        self._link_assoc_class = None
        self._move_assoc_class = None

        self._dict_storage_attribute = {PolarNode: 'nodes', PGLink: 'links', PGMove: 'moves'}
        self._dict_assoc_class = None

        self._find_function = self.default_find_function  # getter
        self._filter_function = self.default_filter_function  # getter
        self._access_function = self.default_access_function  # setter
        self._curr_context = {}

    @property
    @strictly_typed
    def base_polar_graph(self) -> BasePolarGraph:
        return self._base_polar_graph

    @staticmethod
    def default_find_function(x):
        return x.name

    @staticmethod
    def default_filter_function(x):
        return x.active

    @staticmethod
    def default_access_function(x, val):
        x.str_value = val

    @property
    # @strictly_typed
    def cell_dicts(self) -> dict[Union[PolarNode, PGLink, PGMove], dict[str, Cell]]:
        return copy(self._cell_dicts)

    @strictly_typed
    def get_old_link_change_associations(self, link_before: PGLink,
                                         moves_before: tuple[PGMove, PGMove],
                                         old_am: Optional[AssociationsManager] = None) \
            -> tuple[Optional[dict[str, Cell]], dict[PGMove, dict[str, Cell]]]:
        am = old_am if old_am else self
        link_dict = None
        if link_before in am.cell_dicts:
            link_dict = am.cell_dicts[link_before]
        move_dict = {}
        for move in moves_before:
            if move in am.cell_dicts:
                move_dict[move] = am.cell_dicts[move]
        return link_dict, move_dict

    @strictly_typed
    def replace_link_after_node_change(self, link_before: PGLink,
                                       moves_before: tuple[PGMove, PGMove],
                                       link_after: PGLink,
                                       old_am: Optional[AssociationsManager] = None) -> None:
        link_dict, move_dict = self.get_old_link_change_associations(link_before, moves_before, old_am)
        if not (link_dict is None):
            self._cell_dicts[link_after] = link_dict
        ni_s_before = link_before.ni_s
        ni_s_after = link_after.ni_s
        common_ni_s = set(ni_s_before) & set(ni_s_after)
        assert len(common_ni_s) == 1, 'Len of common nis should be 1'
        common_ni = common_ni_s.pop()
        old_not_common_ni = (set(ni_s_before) - {common_ni}).pop()
        new_not_common_ni = (set(ni_s_after) - {common_ni}).pop()
        for old_move in move_dict:
            if old_move.ni is common_ni:
                new_move = common_ni.get_move(link_after)
                self._cell_dicts[new_move] = move_dict[old_move]
                continue
            if old_move.ni is old_not_common_ni:
                new_move = new_not_common_ni.get_move(link_after)
                self._cell_dicts[new_move] = move_dict[old_move]
                continue
            assert False, 'Cannot be variants'

    @strictly_typed
    def replace_link_after_split(self, link_before: PGLink,
                                 moves_before: tuple[PGMove, PGMove],
                                 links_after: tuple[PGLink, PGLink]) -> None:
        link_dict, move_dict = self.get_old_link_change_associations(link_before, moves_before)
        ni_s_before = link_before.ni_s
        ni_s_found = set()
        for link_after in links_after:
            if not (link_dict is None):
                self._cell_dicts[link_after] = link_dict
            for ni in ni_s_before:
                if ni in link_after.ni_s:
                    ni_s_found.add(ni)
                    move_after = ni.get_move(link_after)
                    for move in move_dict:
                        if ni is move.ni:
                            self._cell_dicts[move_after] = move_dict[move]
        assert ni_s_found == set(link_before.ni_s), 'Not all ni_s found'

    @strictly_typed
    def aggregate_refresh_cells(self, old_am: AssociationsManager,
                                elements: Iterable[Union[PolarNode, PGLink, PGMove]]) -> None:
        for element in elements:
            assert element not in self.cell_dicts, 'Element already in current am'
            if element not in old_am.cell_dicts:
                continue
            ocs = old_am.cell_dicts[element]
            self._cell_dicts[element] = ocs

    @strictly_typed
    def refresh_cells_unphysical_nodes_remove(self) -> None:
        for element in self.cell_dicts:
            if isinstance(element, PolarNode) and (element not in self.base_polar_graph.nodes):
                self._cell_dicts.pop(element)

    @strictly_typed
    def create_cell(self, element: Union[PolarNode, PGLink, PGMove],
                    name: str, checker: Optional[CellChecker] = None, str_value: str = '',
                    auto_setter: Optional[AutoValueSetter] = None,
                    context: Optional[str] = None) -> Cell:
        if not (context is None):
            assert context in self.dict_assoc_class[type(element)].possible_strings, \
                'Context {} not found'.format(context)
        else:
            poss_str = self.dict_assoc_class[type(element)].possible_strings
            assert len(poss_str) == 1, \
                'Context should be specified, more then 1 values: {}'.format(poss_str)
            context = set(poss_str).pop()
        if not (element in self.cell_dicts):
            self._cell_dicts[element] = {}
        assert not (context in self.cell_dicts[element]), 'Context {} for element {} already exists'.format(context,
                                                                                                            element)
        cell = Cell(name, str_value, checker, auto_setter)
        self.cell_dicts[element][context] = cell
        return cell

    @property
    @strictly_typed
    def curr_context(self) -> dict[Type[Union[PolarNode, PGLink, PGMove]], set[str]]:
        return {key: copy(val) for key, val in self._curr_context.items()}

    @strictly_typed
    def clear_curr_context(self) -> None:
        self._curr_context.clear()

    @strictly_typed
    def auto_set_curr_context(self) -> None:
        self.clear_curr_context()
        for t, cls in self.dict_assoc_class.items():
            if not (cls is None):
                self._curr_context[t] = set(cls.possible_strings)

    @strictly_typed
    def add_to_curr_context(self, key: Type[Union[PolarNode, PGLink, PGMove]], value: str) -> None:
        if key not in self._curr_context:
            self._curr_context[key] = set()
        self._curr_context[key].add(value)

    @strictly_typed
    def pop_from_curr_context(self, key: Type[Union[PolarNode, PGLink, PGMove]], value: str) -> None:
        self._curr_context[key].pop(value)

    @property
    @strictly_typed
    def filter_function(self) -> Callable:
        return self._filter_function

    @filter_function.setter
    @strictly_typed
    def filter_function(self, value: Callable) -> None:
        self._filter_function = value

    @property
    @strictly_typed
    def find_function(self) -> Callable:
        return self._find_function

    @find_function.setter
    @strictly_typed
    def find_function(self, value: Callable) -> None:
        self._find_function = value

    @property
    @strictly_typed
    def access_function(self) -> Callable:
        return self._access_function

    @access_function.setter
    @strictly_typed
    def access_function(self, value: Callable) -> None:
        self._access_function = value

    @property
    @strictly_typed
    def node_assoc_class(self) -> Optional[Type[NodeAssociation]]:
        return self._node_assoc_class

    @node_assoc_class.setter
    @strictly_typed
    def node_assoc_class(self, value: Type[NodeAssociation]) -> None:
        assert self._node_assoc_class is None, 'Node assoc class is already defined'
        self._node_assoc_class = value

    @property
    @strictly_typed
    def link_assoc_class(self) -> Optional[Type[LinkAssociation]]:
        return self._link_assoc_class

    @link_assoc_class.setter
    @strictly_typed
    def link_assoc_class(self, value: Type[LinkAssociation]) -> None:
        assert self._link_assoc_class is None, 'Link assoc class is already defined'
        self._link_assoc_class = value

    @property
    @strictly_typed
    def move_assoc_class(self) -> Optional[Type[MoveAssociation]]:
        return self._move_assoc_class

    @move_assoc_class.setter
    @strictly_typed
    def move_assoc_class(self, value: Type[MoveAssociation]) -> None:
        assert self._move_assoc_class is None, 'Move assoc class is already defined'
        self._move_assoc_class = value

    @property
    @strictly_typed
    def dict_storage_attribute(self) -> dict[Type[Union[PolarNode, PGLink, PGMove]], str]:
        return self._dict_storage_attribute

    @property
    @strictly_typed
    def dict_assoc_class(self) -> dict[Type[Union[PolarNode, PGLink, PGMove]],
                                       Optional[Type[Union[NodeAssociation, LinkAssociation, MoveAssociation]]]]:
        return {PolarNode: self.node_assoc_class, PGLink: self.link_assoc_class, PGMove: self.move_assoc_class}

    @strictly_typed
    def get_elm_cell_by_context(self, element: Union[PolarNode, PGLink, PGMove], context: Optional[str] = None) \
            -> Optional[Cell]:
        if element not in self.cell_dicts:
            return
        if context is None:
            assert len(self.cell_dicts[element]) == 1, 'Context of element {} should be specified'.format(element)
            return set(self.cell_dicts[element].values()).pop()
        return self.cell_dicts[element][context]

    @strictly_typed
    def get_single_elm_by_cell_content(self, element_type: Type[Union[PolarNode, PGLink, PGMove]],
                                       searched_value: Any,
                                       given_elements: Optional[Iterable[Union[PolarNode, PGLink, PGMove]]] = None,
                                       not_found_assertion: bool = False) \
            -> Optional[Union[PolarNode, PGLink, PGMove]]:
        if given_elements is None:
            storage = getattr(self.base_polar_graph, self.dict_storage_attribute[element_type])
        else:
            assert all([issubclass(type(elt), element_type) for elt in given_elements]), 'Type <> type(elts)'
            storage = given_elements
        found_elements = set()
        assert element_type in self.curr_context, 'Context not initialized for {}'.format(element_type)
        context_set = self.curr_context[element_type]
        assert len(context_set) == 1, 'More then 1 context in context set'
        context = context_set.pop()
        for element in storage:
            context_result = self.get_elm_cell_by_context(element, context)
            if context_result is None:
                continue
            func_value = self.find_function(context_result)
            if func_value == searched_value:
                found_elements.add(element)
        if not found_elements:
            if not_found_assertion:
                assert found_elements, 'Element {} not found'.format(searched_value)
            else:
                return None
        assert len(found_elements) == 1, 'More then 1 element was found'
        return found_elements.pop()

    @strictly_typed
    def get_filter_all_cells(self, element_type: Type[Union[PolarNode, PGLink, PGMove]],
                             given_elements: Optional[Iterable[Union[PolarNode, PGLink, PGMove]]] = None)\
            -> set[Union[PolarNode, PGLink, PGMove]]:
        if given_elements is None:
            storage = getattr(self.base_polar_graph, self.dict_storage_attribute[element_type])
        else:
            assert all([issubclass(type(elt), element_type) for elt in given_elements]), 'Type <> type(elts)'
            storage = given_elements
        found_elements = set()
        assert element_type in self.curr_context, 'Context not initialized for {}'.format(element_type)
        context_set = self.curr_context[element_type]
        assert len(context_set) == 1, 'More then 1 context in context set'
        context = context_set.pop()
        for element in storage:
            context_result = self.get_elm_cell_by_context(element, context)
            if context_result is None:
                continue
            func_value = self.filter_function(context_result)
            if func_value:
                found_elements.add(element)
        return found_elements

    @strictly_typed
    def apply_sbg_content(self, element_type: Type[Union[PolarNode, PGLink, PGMove]],
                          value: Any, subgraph: PolarGraph = None) -> None:
        if not subgraph:
            subgraph = self.base_polar_graph
        storage: set[Union[PolarNode, PGLink, PGMove]] = getattr(subgraph, self.dict_storage_attribute[element_type])
        assert self.curr_context[element_type], 'Context of {} not defined'.format(element_type)
        assert len(self.curr_context[element_type]) == 1, 'More then 1 str_value of context {}'.format(element_type)
        context = self.curr_context[element_type].pop()
        for element in storage:
            if (element not in self.cell_dicts) or (context not in self.cell_dicts[element]):
                continue
            cell = self.cell_dicts[element][context]
            self.access_function(cell, value)

    @strictly_typed
    def extract_route_content(self, route: PGRoute) -> list[set[Cell]]:
        result = []
        # for i in self.cell_dicts:
        #     print('cell_dict = ', i)
        for element in route.sequence:
            element_result = set()
            # print('element = ', element)
            if (type(element) not in self.curr_context) or (element not in self.cell_dicts):
                continue
            contexts_set = self.curr_context[type(element)]
            for context in contexts_set:
                if context not in self.cell_dicts[element]:
                    continue
                element_result.add(self.cell_dicts[element][context])
            result.append(element_result)
        return result


if __name__ == '__main__':

    class GlobalNamesManager:
        def __init__(self):
            self._name_to_obj: dict[str, Any] = {}
            self._obj_to_name: dict[Any, str] = {}

        def register_obj_name(self, obj, name):
            if type(obj) == str:
                obj, name = name, obj
            assert name not in self.name_to_obj, 'Name repeating'
            assert obj not in self.obj_to_name, 'Obj repeating'
            assert not (obj is None), 'None str_value cannot be registered'
            self._name_to_obj[name] = obj
            self._obj_to_name[obj] = name

        def remove_obj_name(self, obj_or_name):
            obj, name = (self.name_to_obj[obj_or_name], obj_or_name) if type(obj_or_name) == str \
                else (obj_or_name, self.obj_to_name[obj_or_name])
            self._name_to_obj.pop(name)
            self._obj_to_name.pop(obj)

        def rename_obj(self, obj, new_name):
            self.remove_obj_name(obj)
            self.register_obj_name(obj, new_name)

        def check_new_name(self, name):
            return not (name in self.name_to_obj)

        @property
        def name_to_obj(self) -> dict[str, Any]:
            return copy(self._name_to_obj)

        @property
        def obj_to_name(self) -> dict[Any, str]:
            return copy(self._obj_to_name)


    GNM = GlobalNamesManager()

    class NameDescriptor:

        def __init__(self, start_index=1):
            assert type(start_index) == int, 'Start index must be int'
            self.start_index = start_index

        def __get__(self, instance, owner=None):
            if instance is None:
                return owner.__name__
            else:
                if hasattr(instance, '_name'):
                    return instance._name
                else:
                    prefix = instance.__class__.__name__ + '_'
                    i = self.start_index
                    while True:
                        if i < 1:
                            name_candidate = '{}{}'.format(prefix, '0' * (1 - i))
                        else:
                            name_candidate = '{}{}'.format(prefix, i)
                        if GNM.check_new_name(name_candidate):
                            break
                        else:
                            i += 1
                    instance._name = name_candidate
                    GNM.register_obj_name(instance, name_candidate)
                    return instance._name


    def init_get_name(old_init):
        def wrapper(*args, **kwargs):
            old_init(*args, **kwargs)
            args[0].name
            return
        return wrapper


    PolarNode.name = NameDescriptor(-1)
    PolarNode.__init__ = init_get_name(PolarNode.__init__)
    PolarNode.__str__ = lambda x: x.name
    PolarNode.__repr__ = lambda x: x.name
    BasePolarGraph.name = NameDescriptor()
    BasePolarGraph.__str__ = lambda x: x.name
    BasePolarGraph.__repr__ = lambda x: x.name
    PolarGraph.name = NameDescriptor()
    PolarGraph.__str__ = lambda x: x.name
    PolarGraph.__repr__ = lambda x: x.name

    test = 'test_2'
    if test == 'test_1':
        pass

    if test == 'test_2':
        def create_graph_1():
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu,
                                                      make_pu_stable=True, make_nd_stable=True)
            pn_2, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_3, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_4, _, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_5, _, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            nodes.extend([pn_1, pn_2, pn_3, pn_4, pn_5])
            return pg_0, nodes


        def create_graph_2():
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_2, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_3, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_4, _, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_5, _, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            nodes.extend([pn_1, pn_2, pn_3, pn_4, pn_5])
            return pg_0, nodes


        def create_graph_3():
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_pu.ni_nd)
            nodes.extend([pn_1])
            return pg_0, nodes


        def create_graph_4():
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_2, _, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pn_1.ni_pu)
            pn_3, _, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pn_2.ni_pu)
            nodes.extend([pn_1, pn_2, pn_3])
            return pg_0, nodes


        def create_graph_5() -> tuple[PolarGraph, list[PolarNode]]:
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu,
                                                      make_nd_stable=True)
            pn_2, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_nd.ni_pu, pn_1.ni_nd)
            pg_0.connect_nodes(pg_0.inf_node_nd.ni_pu, pn_2.ni_nd)
            pn_3, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pn_2.ni_pu)
            nodes.extend([pn_1, pn_2, pn_3])
            return pg_0, nodes


        def create_graph_6():
            pg_0 = BasePolarGraph()
            nodes = ['zero_element']
            pn_1, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_2, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_3, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
            pn_4, _, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            pn_5, _, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
            nodes.extend([pn_1, pn_2, pn_3, pn_4, pn_5])
            return pg_0, nodes


        pg_00, nodes_00 = create_graph_2()

        def nod(num):
            return GNM.name_to_obj['PolarNode_{}'.format(num)]

        print(pg_00)
        print(pg_00.nodes)
        print(nod(2))
        print(pg_00.links)
        print(len(pg_00.links))

        sbg = pg_00.cut_subgraph([nod(3), nod(4), nod(5)], True)  # node(2), node(3),
        print(sbg.nodes)
        print(len(sbg.links))
        print(sbg.border_ni_s)

        # pg_00.remove_nodes([nod(2)])
        # print('after remove node 2')
        # print(pg_00.nodes)
        # print(pg_00.links)
        # print(len(pg_00.links))
        #
        # pg_00.remove_nodes([nod(3)])
        # print('after remove node 3')
        # print(pg_00.nodes)
        # print(pg_00.links)
        # print(len(pg_00.links))
        #
        # pg_00.remove_nodes([nod(4)])
        # print('after remove node 4')
        # print(pg_00.nodes)
        # print(pg_00.links)
        # print(len(pg_00.links))
        #
        # pg_00.remove_nodes([nod(5)])
        # print('after remove node 5')
        # print(pg_00.nodes)
        # print(pg_00.links)
        # print(len(pg_00.links))

        # pg_00.remove_nodes([nod(1)])
        # print('after remove node 1')
        # print(pg_00.nodes)
        # print(pg_00.links)
        # print(len(pg_00.links))

        # pg_00.remove_nodes([nod(1), nod(2), nod(3), nod(4), nod(5)])
        # print('after remove node 1-5')
        # print(pg_00.nodes)
        # print(pg_00.links)
        # print(len(pg_00.links))

        # pg_10 = deepcopy(pg_00)
        # print(pg_10.layered_representation(pg_10.inf_node_pu.ni_nd))
        # pg_00.aggregate(pg_10)
        # pg_00l = pg_00.layered_representation(pg_00.inf_node_pu.ni_nd)
        # pg_10l = pg_10.layered_representation(pg_10.inf_node_pu.ni_nd)
        # print(pg_00l)
        # print(pg_10l)
        # print(len(pg_00.links))

        # subgraph_: PolarGraph = pg_00.cut_subgraph([nodes_00[2], nodes_00[3], nodes_00[1]])
        # print(pg_00.links)
        # pg_00.am.apply_sbg_content(PGLink, 'link_assoc', 0., subgraph_)
        # pg_00.am.apply_sbg_content(PolarNode, 'node_assoc', 100, subgraph_)
        # print(pg_00.am.extract_sbg_content({PGLink: 'link_assoc', PolarNode: 'node_assoc'},
        #                                    subgraph_))

        # route_: PGRoute = pg_00.free_roll(pg_00.inf_node_pu.ni_nd)
        # print(route_)
        # print(route_.route_begin, route_.route_end)

        # route_from_to_: PGRoute = pg_00.find_single_route(pg_00.inf_node_pu, pg_00.inf_node_nd,
        #                                                   [nodes_00[2], nodes_00[4]])
        # pg_00.associations.apply_sbg_content(PolarNode, 'node_assoc', 300, route_from_to_)
        # route_result_ = pg_00.associations.extract_route_content({PGLink: 'link_assoc', PolarNode: 'node_assoc'},
        #                                                          route_from_to_)
        # print(route_result_)

        # i = 0
        # for node_ in pg_00.nodes:
        #     i += 1
        #     node_.associations['node_assoc'] = i
        #     node_.associations['string'] = str(i)
        #     print(node_.associations)
        # for link_ in pg_00.links:
        #     i += 1
        #     link_.associations['link_assoc'] = float(i)
        #     print(link_.associations)
        # for move_ in pg_00.moves:
        #     i += 1
        #     move_.associations['move_assoc'] = str(i)
        #     print(move_.associations)

        # print(pg_00.associations.get_element_by_content_value(PolarNode, 'node_assoc', 5))

        # subgraph_: PolarGraph = pg_00.cut_subgraph([nodes_00[2], nodes_00[3], nodes_00[1]])
        # pg_00.associations.apply_sbg_content(PGLink, 'link_assoc', 0., subgraph_)
        # pg_00.associations.apply_sbg_content(PolarNode, 'node_assoc', 100, subgraph_)
        #
        # for node_ in pg_00.nodes:
        #     print(node_.associations)
        # for link_ in pg_00.links:
        #     print(link_.associations)
        # for move_ in pg_00.moves:
        #     print(move_.associations)

        # for ni_ in link_.ni_s:
        #     for move_ in ni_.moves:
        #         move_.associations['move_assoc'] = str(i)
        #         print(move_.associations)

        # routes_ = pg_00.walk_to_borders(pg_00.inf_node_pu.ni_nd)
        # cover_graph: PolarGraph = pg_00.find_node_coverage(nodes_00[1].ni_pu, [nodes_00[2], nodes_00[3]])
        # subgraph_: PolarGraph = pg_00.cut_subgraph([nodes_00[2], nodes_00[3], nodes_00[4], nodes_00[5]])
        # routes_pn1_pn2_: set[PGRoute] = pg_00.find_routes(pg_00.inf_node_pu, nodes_00[1])

        # route_from_to_: PGRoute = pg_00.find_single_route(pg_00.inf_node_pu, pg_00.inf_node_nd,
        #                                                   [nodes_00[2], nodes_00[4]])
        # pg_00.activate_route(route_from_to_)

        # i = 0
        # for node_ in route_from_to_.nodes:
        #     i += 1
        #     node_.associations = 'ups'
        #     node_.associations['my_key'] = str(i)
        # for node_ in route_from_to_.nodes:
        #     print('node associations = ', node_.associations)

        # for move_ in route_from_to_.moves:
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

    if test == 'test_4':
        pass

    if test == 'test_5':
        pass

    if test == 'test_6':
        pass
