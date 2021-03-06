from __future__ import annotations
from itertools import combinations
from collections import OrderedDict, namedtuple
from typing import Optional, Union, Any, Type
from collections.abc import Iterable
from copy import copy, deepcopy

from cell_object import CellObject, ListCO
from custom_enum import CustomEnum
from extended_itertools import flatten


class End(CustomEnum):
    negative_down = 0
    nd = 0
    positive_up = 1
    pu = 1


class Element:
    def __init__(self):
        self._cell_objs: list[CellObject] = []

    @property
    def cell_objs(self) -> list[CellObject]:
        return self._cell_objs

    @cell_objs.setter
    def cell_objs(self, val: list[CellObject]):
        self._cell_objs = val

    def append_cell_obj(self, cell_obj: CellObject):
        self._cell_objs.append(cell_obj)

    def remove_cell_obj(self, cell_obj: CellObject):
        self._cell_objs.remove(cell_obj)

    def copy_cells(self, deep: bool = True) -> list[CellObject]:
        cell_objs = self._cell_objs
        if deep:
            cell_objs = [co.copy() for co in self._cell_objs]
        return cell_objs


class NodeInterface:
    def __init__(self, pn: PolarNode, end: End) -> None:
        self._pn = pn
        self._end = end
        self._move_by_link: OrderedDict[Link, Move] = OrderedDict()

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.pn, self.end)

    __str__ = __repr__

    @property
    def pn(self) -> PolarNode:
        return self._pn

    @property
    def end(self) -> End:
        return self._end

    @property
    def end_str(self) -> str:
        if self.end == "nd":
            return "nd"
        else:
            return "pu"

    @property
    def opposite_end_str(self) -> str:
        if self.end == "nd":
            return "pu"
        else:
            return "nd"

    @property
    def links(self) -> list[Link]:
        return list(self._move_by_link.keys())

    @property
    def moves(self) -> list[Move]:
        return list(self._move_by_link.values())

    def get_move_by_link(self, link: Link) -> Move:
        return self._move_by_link[link]

    def add_link(self, link: Link) -> None:
        assert link not in self.links, 'Link already connected'
        self._move_by_link[link] = Move(self, link)
        self.random_move_activate()

    def remove_link(self, link: Link) -> None:
        self._move_by_link.pop(link)
        self.random_move_activate()

    def choice_move_activate(self, move: Move) -> None:
        assert move in self.moves, 'Move not found'
        self._deactivate_all_moves()
        move.active = True

    def random_move_activate(self):
        self._deactivate_all_moves()
        if self.moves:
            move_random = set(self.moves).pop()
            move_random.active = True

    def _deactivate_all_moves(self):
        for move in self.moves:
            move.active = False

    @property
    def is_empty(self) -> bool:
        return len(self._move_by_link) == 0

    @property
    def active_move(self) -> Optional[Move]:
        active_moves = set(filter(lambda item: item.active, self.moves))
        assert len(active_moves) <= 1, 'Only <= 1 Move should be active'
        if active_moves:
            return active_moves.pop()


class Move(Element):
    def __init__(self, ni: NodeInterface, link: Link) -> None:
        super().__init__()
        self._link = link
        self._ni = ni
        self.active = False

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.ni, self.link)

    __str__ = __repr__

    @property
    def link(self) -> Link:
        return self._link

    @property
    def ni(self) -> NodeInterface:
        return self._ni


class Link(Element):
    def __init__(self, ni_1: NodeInterface, ni_2: NodeInterface) -> None:
        super().__init__()
        self._ni_s = (ni_1, ni_2)
        ni_1.add_link(self)
        ni_2.add_link(self)

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.ni_s[0], self.ni_s[1])

    __str__ = __repr__

    @property
    def ni_s(self) -> tuple[NodeInterface, NodeInterface]:
        return self._ni_s

    def opposite_ni(self, given_ni: NodeInterface) -> NodeInterface:
        assert given_ni in self.ni_s, 'Given ni not found in link'
        return (set(self.ni_s) - {given_ni}).pop()


class CountDescriptor:

    def __get__(self, instance, owner):
        if not hasattr(owner, "_i"):
            owner._i = 0
        if not hasattr(instance, "_ii"):
            owner._i += 1
            instance._ii = owner._i
        return instance._ii

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class PolarNode(Element):
    i = CountDescriptor()

    def __init__(self) -> None:
        super().__init__()
        self._ni_nd, self._ni_pu = NodeInterface(self, End('nd')), NodeInterface(self, End('pu'))
        self._ni_s = (self.ni_nd, self.ni_pu)
        self.i

    def __repr__(self):
        return '{}_{}'.format(self.__class__.__name__, self.i)

    __str__ = __repr__

    @property
    def ni_nd(self) -> NodeInterface:
        return self._ni_nd

    @property
    def ni_pu(self) -> NodeInterface:
        return self._ni_pu

    def ni_by_end(self, end: End) -> NodeInterface:
        if end == 'nd':
            return self.ni_nd
        else:
            return self.ni_pu

    @property
    def ni_s(self) -> tuple[NodeInterface, NodeInterface]:
        return self._ni_s

    @property
    def count_side_connected(self) -> int:
        return 2 - self.ni_nd.is_empty - self.ni_pu.is_empty

    @property
    def only_1_not_empty_ni(self) -> NodeInterface:
        assert self.count_side_connected <= 1, "More then 1 side connected"
        assert self.count_side_connected >= 1, "Less then 1 side connected"
        if self.ni_nd.is_empty:
            return self.ni_pu
        else:
            return self.ni_nd

    def opposite_ni(self, given_ni: NodeInterface) -> NodeInterface:
        assert given_ni in self.ni_s, 'Given ni not found in node'
        return (set(self.ni_s) - {given_ni}).pop()


def common_ni_of_node_link(pn: PolarNode, link: Link) -> NodeInterface:
    assert not (link.ni_s[0].pn is link.ni_s[1].pn), "Event when link connected to pu and nd of 1 node not supported"
    return (set(link.ni_s) & set(pn.ni_s)).pop()


def common_links_of_ni_s(ni_1: NodeInterface, ni_2: NodeInterface) -> set[Link]:
    return set(ni_1.links) & set(ni_2.links)


class Route:

    def __init__(self, start_ni: NodeInterface, links: list[Link] = None):
        self._start_ni = start_ni
        if links is None:
            self._links: list[Link] = []
        else:
            self._links = links

    def __eq__(self, other: Route):
        return (self.start_ni is other.start_ni) and (set(self.nodes) == set(other.nodes))

    def __hash__(self):
        return id(self)

    @property
    def start_ni(self) -> NodeInterface:
        return self._start_ni

    @property
    def links(self) -> list[Link]:
        return copy(self._links)

    @property
    def is_empty(self) -> bool:
        return not self.links

    @property
    def outer_ni_s(self) -> list[NodeInterface]:
        result: list[NodeInterface] = [self.start_ni]
        if self.links:
            for link in self.links[:-1]:
                opposite_link_ni = link.opposite_ni(result[-1])
                result.append(opposite_link_ni.pn.opposite_ni(opposite_link_ni))
        return result

    @property
    def enter_ni_s(self) -> list[NodeInterface]:
        assert not self.is_empty, "Empty link list, no enter ni-s"
        result: list[NodeInterface] = []
        outer_ni_s = self.outer_ni_s
        for i, link in enumerate(self.links):
            result.append(link.opposite_ni(outer_ni_s[i]))
        return result

    @property
    def nodes(self) -> list[PolarNode]:
        """ not most effective implementation """
        outer_nodes = [ni.pn for ni in self.outer_ni_s]
        outer_nodes.append(self.enter_ni_s[-1].pn)  # ...because this
        return outer_nodes

    def append_link(self, link: Link):
        self._links.append(link)

    @property
    def end_outer_ni(self) -> NodeInterface:
        return self.outer_ni_s[-1]

    @property
    def end_enter_ni(self) -> NodeInterface:
        return self.enter_ni_s[-1]

    @property
    def is_cycle(self) -> bool:
        end_pn = self.end_enter_ni.pn
        return end_pn in self.nodes[:-1]

    @property
    def cycle_nodes(self) -> list[PolarNode]:
        assert self.is_cycle
        end_pn = self.end_enter_ni.pn
        loop_begin_index = 0
        for i, node in enumerate(self.nodes[:-1]):
            if node is end_pn:
                loop_begin_index = i
                break
        return self.nodes[loop_begin_index:-1]

    @property
    def cycle_links(self) -> list[Link]:
        assert self.is_cycle
        end_pn = self.end_enter_ni.pn
        loop_begin_index = 0
        for i, node in enumerate(self.nodes[:-1]):
            if node is end_pn:
                loop_begin_index = i
                break
        return self.links[loop_begin_index:]

    def get_slice(self, start_ni: NodeInterface = None, end_enter_ni: NodeInterface = None) -> Route:
        if start_ni is None:
            start_ni = self.start_ni
        if end_enter_ni is None:
            end_enter_ni = self.end_enter_ni
        first_link_index = self.outer_ni_s.index(start_ni)
        try:
            last_link_index = self.enter_ni_s.index(end_enter_ni)
        except ValueError as ve:
            if end_enter_ni.pn is start_ni.pn:
                return Route(start_ni)
            else:
                raise ve
        return Route(start_ni, self.links[first_link_index:last_link_index+1])

    def activate(self):
        for link in self.links:
            for ni in link.ni_s:
                ni.choice_move_activate(ni.get_move_by_link(link))

    def partially_overlaps(self, route_2: Route) -> bool:
        return bool(set(self.links) & set(route_2.links))


class NodesMerge:
    def __init__(self, ni_base: NodeInterface, ni_insert: NodeInterface, merge: bool = True):
        self.ni_base = ni_base
        self.ni_insert = ni_insert
        self.merge = merge


class PolarGraph:

    def __init__(self):
        self._nodes: set[PolarNode] = set()
        self._links: set[Link] = set()
        self._node_copy_mapping: dict[PolarNode, PolarNode] = {}
        self._link_copy_mapping: dict[Link, Link] = {}
        self._move_copy_mapping: dict[Move, Move] = {}

    @property
    def nodes(self) -> set[PolarNode]:
        return copy(self._nodes)

    @property
    def links(self) -> set[Link]:
        return copy(self._links)

    @property
    def node_copy_mapping(self) -> dict[PolarNode, PolarNode]:
        return copy(self._node_copy_mapping)

    @property
    def link_copy_mapping(self) -> dict[Link, Link]:
        return copy(self._link_copy_mapping)

    @property
    def move_copy_mapping(self) -> dict[Move, Move]:
        return copy(self._move_copy_mapping)

    @property
    def border_ni_s(self) -> set[NodeInterface]:
        return {pn.only_1_not_empty_ni for pn in self.nodes if pn.count_side_connected == 1}

    def init_node(self) -> PolarNode:
        pn = PolarNode()
        self._nodes.add(pn)
        return pn

    def connect(self, ni_1: NodeInterface, ni_2: NodeInterface) -> Link:
        link = Link(ni_1, ni_2)
        self._links.add(link)
        return link

    def disconnect(self, ni_1: NodeInterface, ni_2: NodeInterface,
                   not_connect_assert: bool = True, remove_only_one: bool = True) -> None:
        links_1_2 = common_links_of_ni_s(ni_1, ni_2)
        if not_connect_assert:
            assert links_1_2, "Ni_s not connected for disconnect"
        if not links_1_2:
            return
        if remove_only_one:
            links_1_2 = {links_1_2.pop()}
        for link in links_1_2:
            ni_1.remove_link(link)
            ni_2.remove_link(link)
            self._links.remove(link)

    def walk(self, start_ni: NodeInterface, stop_nodes: Iterable[PolarNode] = None) -> list[Route]:
        if stop_nodes is None:
            stop_nodes = set()
        else:
            stop_nodes = set(stop_nodes)
        routes_: list[Route] = [Route(start_ni)]
        links_need_to_check: OrderedDict[NodeInterface, list[Link]] = OrderedDict({start_ni: start_ni.links})
        route_ends = False

        while links_need_to_check:
            last_out_ni = list(links_need_to_check.keys())[-1]
            if not links_need_to_check[last_out_ni]:
                links_need_to_check.pop(last_out_ni)
                if len(links_need_to_check):
                    up_ni = last_out_ni.pn.opposite_ni(last_out_ni)
                    prev_ni = list(links_need_to_check.keys())[-1]
                    common_links = common_links_of_ni_s(up_ni, prev_ni)
                    for common_link in common_links:
                        if common_link in links_need_to_check[prev_ni]:
                            links_need_to_check[prev_ni].remove(common_link)
                            break
            else:
                if route_ends:
                    end_enter_ni = last_out_ni.pn.opposite_ni(last_out_ni)
                    routes_.append(routes_[-1].get_slice(end_enter_ni=end_enter_ni))
                    route_ends = False
                link = links_need_to_check[last_out_ni][0]
                enter_ni = link.opposite_ni(last_out_ni)
                enter_node = enter_ni.pn
                routes_[-1].append_link(link)
                if (enter_node in stop_nodes) or (enter_ni in self.border_ni_s) or \
                        (enter_node in routes_[-1].nodes[:-1]):
                    links_need_to_check[last_out_ni].remove(link)
                    route_ends = True
                else:
                    opposite_ni = enter_node.opposite_ni(enter_ni)
                    links_need_to_check[opposite_ni] = opposite_ni.links
        return routes_

    def routes_node_to_node(self, start_node: PolarNode, end_node: PolarNode) \
            -> tuple[list[Route], Union[bool, NodeInterface]]:
        routes = []
        ni_found = False
        for start_ni in start_node.ni_s:
            new_routes = [route for route in self.walk(start_ni, [end_node]) if (route.nodes[-1] is end_node)]
            if new_routes:
                assert not ni_found, "Second ni found as begin of route to end-node"
                ni_found = start_ni
            routes.extend(new_routes)
        return routes, ni_found

    def route_links_between(self, border_nodes: Iterable[PolarNode], internal_node: PolarNode = None) -> set[Link]:
        border_nodes = set(border_nodes)
        routes_: set[Route] = set()
        for border_node in border_nodes:
            for ni in border_node.ni_s:
                ni_routes = self.walk(ni, border_nodes)
                routes_ |= {route_ for route_ in ni_routes
                            if (not route_.is_empty) and (route_.end_enter_ni.pn in border_nodes)}
        internal_links: set[Link] = set()
        internal_nodes: set[PolarNode] = set()
        for route_ in routes_:
            internal_links |= set(route_.links)
            internal_nodes |= set(route_.nodes)
        if internal_node and internal_node not in internal_nodes:
            return self.links - internal_links
        else:
            return internal_links

    def copy_part(self, links: Iterable[Link] = None, copy_cells: bool = True, deep_copy: bool = True) -> PolarGraph:
        if links is None:
            links = self.links
            nodes = self.nodes
        else:
            """ isolated nodes not will be copied in this case """
            nodes: set[PolarNode] = set()
            for link in links:
                for ni in link.ni_s:
                    nodes.add(ni.pn)
        new_pg = self.__class__()
        if isinstance(new_pg, OneComponentTwoSidedPG):
            self: OneComponentTwoSidedPG
            nodes_images: dict[PolarNode, PolarNode] = \
                {node: new_pg.init_node() for node in nodes if node not in self.inf_nodes}
            nodes_images[self.inf_nd] = new_pg.inf_nd
            nodes_images[self.inf_pu] = new_pg.inf_pu
        else:
            nodes_images: dict[PolarNode, PolarNode] = {node: new_pg.init_node() for node in nodes}
        links_images: dict[Link, Link] = {}
        moves_images: dict[Move, Move] = {}
        for link in links:
            old_ni_1, old_ni_2 = link.ni_s
            old_move_1 = old_ni_1.get_move_by_link(link)
            old_move_2 = old_ni_2.get_move_by_link(link)
            new_ni_1 = nodes_images[old_ni_1.pn].ni_by_end(old_ni_1.end)
            new_ni_2 = nodes_images[old_ni_2.pn].ni_by_end(old_ni_2.end)
            new_link = new_pg.connect(new_ni_1, new_ni_2)
            new_move_1 = new_ni_1.get_move_by_link(new_link)
            new_move_2 = new_ni_2.get_move_by_link(new_link)
            links_images[link] = new_link
            moves_images[old_move_1] = new_move_1
            moves_images[old_move_2] = new_move_2
        for move in moves_images:
            if move.active:
                new_move = moves_images[move]
                new_move.ni.choice_move_activate(new_move)
        if copy_cells:
            for node in nodes_images:
                nodes_images[node].cell_objs = node.copy_cells(deep_copy)
            for link in links_images:
                links_images[link].cell_objs = link.copy_cells(deep_copy)
            for move in moves_images:
                moves_images[move].cell_objs = move.copy_cells(deep_copy)
        new_pg._node_copy_mapping.update(nodes_images)
        new_pg._link_copy_mapping.update(links_images)
        new_pg._move_copy_mapping.update(moves_images)
        return new_pg

    def aggregate(self, insert_graph: PolarGraph,
                  n_merges: Iterable[NodesMerge]) -> None:
        """
        inserted graph need to satisfy 2 conditions:
        1. Inserted interfaces should be empty
        2. If we can build route between ni-s in base graph,
        we can build route from corresponding ni_s in inserted graph
        """
        """
        ! move activation and cells coping for removed nodes and links should be implemented !
        """
        # Stage A. Check conditions
        for n_merge in n_merges:
            assert n_merge.ni_insert.is_empty, "Requirement 1 not satisfied"
        nis_base: dict[NodeInterface, NodesMerge] = {nm.ni_base: nm for nm in n_merges}
        nis_insert: dict[NodeInterface, NodesMerge] = {nm.ni_insert: nm for nm in n_merges}
        merge_nodes_base: set[PolarNode] = {ni.pn for ni in nis_base}
        merge_nodes_insert: set[PolarNode] = {ni.pn for ni in nis_insert}
        for ni_base in nis_base:
            routes_in_base = self.walk(ni_base, merge_nodes_base)
            for route_in_base in routes_in_base:
                if route_in_base.end_enter_ni in nis_base:
                    ni_end_base = route_in_base.end_enter_ni
                    ni_end_insert = nis_base[ni_end_base].ni_insert
                    ni_insert = nis_base[ni_base].ni_insert
                    ni_opposite_end_insert = ni_end_insert.pn.opposite_ni(ni_end_insert)
                    ni_opposite_insert = ni_insert.pn.opposite_ni(ni_insert)
                    routes_in_insert = insert_graph.walk(ni_opposite_insert, merge_nodes_insert)
                    assert any([route_in_insert.end_enter_ni is ni_opposite_end_insert
                                for route_in_insert in routes_in_insert]), \
                        "Requirement 2 not satisfied"

        # Stage B. Base graph preparation
        for ni_pair in combinations(nis_base, 2):
            common_links = common_links_of_ni_s(*ni_pair)
            if common_links:
                self.disconnect(*ni_pair, remove_only_one=False)
        excluded_nodes: set[PolarNode] = set()
        excluded_links: set[Link] = set()
        for ni_insert in nis_insert:
            if nis_insert[ni_insert].merge:
                excluded_nodes.add(ni_insert.pn)
                excluded_links |= set(ni_insert.pn.opposite_ni(ni_insert).links)
        self._nodes |= (insert_graph.nodes - excluded_nodes)
        self._links |= (insert_graph.links - excluded_links)

        # Stage C. Connection
        for n_merge in n_merges:
            if not n_merge.merge:
                self.connect(n_merge.ni_base, n_merge.ni_insert)
            else:
                node_insert = n_merge.ni_insert.pn
                internal_ni = node_insert.opposite_ni(n_merge.ni_insert)
                internal_opposite_ni_s = {lnk.opposite_ni(internal_ni) for lnk in internal_ni.links}
                for internal_opposite_ni in internal_opposite_ni_s:
                    insert_graph.disconnect(internal_ni, internal_opposite_ni, remove_only_one=False)
                    self.connect(n_merge.ni_base, internal_opposite_ni)

        # Stage D. Activation


class OneComponentTwoSidedPG(PolarGraph):
    def __init__(self):
        super().__init__()
        self.inf_pu = self.init_node()
        self.inf_nd = self.init_node()

    @property
    def inf_ni_s(self):
        return self.inf_pu.ni_nd, self.inf_nd.ni_pu

    @property
    def inf_nodes(self):
        return self.inf_pu, self.inf_nd

    @property
    def not_inf_nodes(self):
        return self.nodes - set(self.inf_nodes)

    @property
    def nodes_inf_connected(self) -> dict[PolarNode, NodeInterface]:
        result = {}
        for ni in self.inf_ni_s:
            for link in ni.links:
                opposite_ni = link.opposite_ni(ni)
                result[opposite_ni.pn] = opposite_ni
        return result

    @property
    def not_inf_links(self):
        result = self.links
        for link in self.links:
            for ni in link.ni_s:
                if ni in self.inf_ni_s:
                    result.remove(link)
        return result

    def insert_node(self, ni_pu: NodeInterface = None, ni_nd: NodeInterface = None,
                    remove_exist_link: bool = True) -> PolarNode:
        if ni_pu is None:
            ni_pu = self.inf_pu.ni_nd
        if ni_nd is None:
            ni_nd = self.inf_nd.ni_pu
        if remove_exist_link:
            self.disconnect(ni_pu, ni_nd, False)
        new_node = self.init_node()
        self.connect(ni_pu, new_node.ni_pu)
        self.connect(ni_nd, new_node.ni_nd)
        return new_node

    def connect_inf_handling(self, ni_1: NodeInterface, ni_2: NodeInterface) -> Link:
        link = self.connect(ni_1, ni_2)
        for ni in ni_1, ni_2:
            for ni_inf in self.inf_ni_s:
                if common_links_of_ni_s(ni, ni_inf):
                    self.disconnect(ni, ni_inf)
        return link

    def disconnect_inf_handling(self, ni_1: NodeInterface, ni_2: NodeInterface):
        inf_dict: dict[NodeInterface, NodeInterface] = {}
        for ni in ni_1, ni_2:
            routes = self.walk(ni)
            ni_inf_found = {route.end_enter_ni for route in routes}
            assert len(ni_inf_found) == 1, "Walk leads to different inf nodes"
            ni_inf = ni_inf_found.pop()
            assert ni_inf in self.inf_ni_s, "Ni inf not in graph inf ni_s"
            inf_dict[ni] = ni_inf
        self.disconnect(ni_1, ni_2)
        for ni in ni_1, ni_2:
            if ni.is_empty:
                self.connect(ni, inf_dict[ni])

    def insert_node_neck(self, necked_ni: NodeInterface = None) -> PolarNode:
        if not necked_ni:
            necked_ni = self.inf_nd.ni_pu
        opposite_ni_s = {link.opposite_ni(necked_ni) for link in necked_ni.links}
        new_node = self.init_node()
        self.connect(new_node.ni_nd, necked_ni)
        for opposite_ni in opposite_ni_s:
            self.disconnect(necked_ni, opposite_ni)
            self.connect(new_node.ni_pu, opposite_ni)
        return new_node

    def free_roll(self, start_ni: NodeInterface = None) -> Route:
        if not start_ni:
            start_ni = self.inf_pu.ni_nd
        route = Route(start_ni)
        current_ni = start_ni
        while True:
            if current_ni.is_empty:
                break
            if not current_ni.active_move:
                current_ni.random_move_activate()
            link = current_ni.active_move.link
            opposite_ni = link.opposite_ni(current_ni)
            node = opposite_ni.pn
            route.append_link(link)
            current_ni = node.opposite_ni(opposite_ni)
        return route

    def shortest_coverage(self, start_ni: NodeInterface = None) -> list[list[PolarNode]]:
        if not start_ni:
            start_ni = self.inf_pu.ni_nd
        last_ni_s: list[NodeInterface] = [start_ni]
        layers: list[list[PolarNode]] = []
        if start_ni.pn not in self.inf_nodes:
            layers.append([start_ni.pn])
        while last_ni_s:
            new_last_ni_s = []
            layers.append([])
            for last_ni in last_ni_s:
                for link in last_ni.links:
                    opposite_ni = link.opposite_ni(last_ni)
                    pn = opposite_ni.pn
                    if pn in self.inf_nodes:
                        continue
                    if pn not in flatten(layers):
                        layers[-1].append(pn)
                        new_last_ni_s.append(pn.opposite_ni(opposite_ni))
            last_ni_s = new_last_ni_s
        if not layers[-1]:
            layers.pop()
        return layers

    def longest_coverage(self, start_ni: NodeInterface = None) -> list[list[PolarNode]]:
        """ returns nodes in order from min longest root to max l.r. """
        if not start_ni:
            start_ni = self.inf_pu.ni_nd
        routes = self.walk(start_ni)
        layers: list[list[PolarNode]] = []
        for route in routes:
            i = 0
            for node in route.nodes:
                if node in self.inf_nodes:
                    continue
                i += 1
                if len(layers) < i:
                    layers.append([])
                if node not in layers[i-1]:
                    layers[i-1].append(node)
        nodes = set()
        for i, rev_layer in enumerate(list(reversed(layers))):
            nodes_for_remove = []
            for node in rev_layer:
                if node in nodes:
                    nodes_for_remove.append(node)
            for node in nodes_for_remove:
                rev_layer.remove(node)
            nodes |= set(rev_layer)
        return layers

    def closed_links_nodes(self, border_nodes: Iterable[PolarNode]) -> tuple[set[Link], set[PolarNode]]:
        border_nodes = set(border_nodes)
        route_links = self.route_links_between(border_nodes)
        internal_nodes = set()
        for link in route_links:
            for ni in link.ni_s:
                if ni.pn in border_nodes:
                    continue
                internal_nodes.add(ni.pn)
                routes = self.walk(ni, border_nodes)
                if any([route.end_enter_ni in self.inf_ni_s for route in routes]):
                    return set(), set()
        return route_links, internal_nodes


if __name__ == '__main__':
    pass
    # pg = PolarGraph()
    # pn_1 = pg.init_node()
    # pn_2 = pg.init_node()
    # pn_3 = pg.init_node()
    # pn_4 = pg.init_node()
    # pn_5 = pg.init_node()
    # pn_6 = pg.init_node()
    # pn_7 = pg.init_node()
    # pg.connect(pn_1.ni_nd, pn_2.ni_pu)
    # pg.connect(pn_1.ni_nd, pn_3.ni_pu)
    # pg.connect(pn_3.ni_nd, pn_4.ni_pu)
    # pg.connect(pn_2.ni_nd, pn_4.ni_pu)
    # pg.connect(pn_4.ni_nd, pn_5.ni_pu)
    # pg.connect(pn_4.ni_nd, pn_6.ni_pu)
    # pg.connect(pn_5.ni_nd, pn_7.ni_pu)
    # pg.connect(pn_6.ni_nd, pn_7.ni_pu)

    # routes = pg.walk(pn_1.ni_nd, [pn_1])
    # print(routes)
    # for route in routes:
    #     print("elements", route.elements)
    # print(pg.links_between([pn_2, pn_3, pn_5, pn_6], pn_2))

    # pg = PolarGraph()
    # pn_1 = pg.init_node()
    # a = ListCO()
    # pn_1.append_cell_obj(a)
    # pn_2 = pg.init_node()
    # pn_2.cell_objs = pn_1.copy_cells(False)
    # print(pn_1.cell_objs)
    # print(pn_2.cell_objs)

    # pg_copy = pg.copy_part(pg.links_between([pn_2, pn_3, pn_5, pn_6]))
    # print(pg_copy.nodes)
    # print(len(pg_copy.links))
    # print(pg_copy.links)

    # pg_2 = PolarGraph()
    # pn_8 = pg_2.init_node()
    # pn_9 = pg_2.init_node()
    # pn_10 = pg_2.init_node()
    # pn_11 = pg_2.init_node()
    # pn_12 = pg_2.init_node()
    # pn_13 = pg_2.init_node()
    # pg_2.connect(pn_8.ni_nd, pn_9.ni_pu)
    # pg_2.connect(pn_9.ni_nd, pn_10.ni_pu)
    # pg_2.connect(pn_9.ni_nd, pn_11.ni_pu)
    # pg_2.connect(pn_10.ni_nd, pn_12.ni_pu)
    # pg_2.connect(pn_11.ni_nd, pn_12.ni_pu)
    # pg_2.connect(pn_12.ni_nd, pn_13.ni_pu)
    # pg_2_copy = pg_2.copy_part()
    # pg.aggregate(pg_2_copy, [NodesMerge(pn_4.ni_nd, pg_2_copy.node_copy_mapping[pn_8].ni_pu, True),
    #                                 NodesMerge(pn_6.ni_pu, pg_2_copy.node_copy_mapping[pn_13].ni_nd, True)])
    # print(len(pg.nodes))
    # print(pg.nodes)
    # print(len(pg.links))
    # print(pg.links)

    pg_3 = OneComponentTwoSidedPG()
    pn_3 = pg_3.insert_node()
    pn_4 = pg_3.insert_node()
    pn_5 = pg_3.insert_node()
    pn_6 = pg_3.insert_node(pn_3.ni_nd)
    pn_7 = pg_3.insert_node(pn_3.ni_nd)
    pn_8 = pg_3.insert_node(pn_4.ni_nd)
    pn_9 = pg_3.insert_node(pn_5.ni_nd)
    pn_10 = pg_3.insert_node(pn_5.ni_nd)
    pn_11 = pg_3.insert_node(pn_5.ni_nd)
    pn_12 = pg_3.insert_node_neck()
    pn_13 = pg_3.insert_node_neck(pg_3.inf_pu.ni_nd)
    pg_3.connect(pn_5.ni_nd, pn_12.ni_pu)
    # pn_13 = pg_3.insert_node_neck()

    # print(pg_3.shortest_coverage())
    print(pg_3.longest_coverage())
    # routs = pg_3.walk(pg_3.inf_pu.ni_nd)
    # print(len(routs))
    # print(routs)
    # lb = pg_3.route_links_between([pn_5])
    # print(len(lb))
    # print(lb)
    #
    # print(pg_3.free_roll().nodes)

    cl = pg_3.closed_links_nodes([pn_8, pn_13])
    print(len(cl))
    print(cl)
    print("route_exists =", pg_3.routes_node_to_node(pn_12, pn_13))
    print("inf connected =", pg_3.nodes_inf_connected)
    print("links common len =", len(pg_3.links))
    print("links not inf len =", len(pg_3.not_inf_links))

    # print(pg_3.free_roll().nodes)

    # pg = OneComponentTwoSidedPG()
    # node = pg.insert_node()
    #
    # pg_3.aggregate(pg, [NodesMerge(pn_3.ni_nd, pg.inf_pu.ni_pu),
    #                     NodesMerge(pn_6.ni_pu, pg.inf_nd.ni_nd)])
