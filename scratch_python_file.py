from __future__ import annotations

from nv_typing import *
from nv_names_control import names_control
from nv_string_set_class import bounded_string_set, BoundedStringSet
from nv_polar_graph import (BasePolarGraph,
                            PolarNode,
                            PGLink,
                            PGMove,
                            End,
                            PGRoute)  #
from nv_attribute_format import BSSAttributeType, AttributeFormat
from nv_associations import AttribNodeAssociation, AttribMoveAssociation
from nv_typed_cell import NamedCell, TypedCell
from copy import copy, deepcopy
import re

BSSDependency = bounded_string_set('BSSDependency', [['dependent'], ['independent']])
BSSBool = bounded_string_set('BSSBool', [['True'], ['False']])


class GlobalNameObjectMapping:
    def __init__(self):
        self._name_to_obj: dict[str, Any] = {}
        self._obj_to_name: dict[Any, str] = {}

    def register_obj_name(self, obj, name):
        assert name not in self.name_to_obj, 'Name repeating'
        assert obj not in self.obj_to_name, 'Obj repeating'
        self._name_to_obj[name] = obj
        self._obj_to_name[obj] = name

    def remove_obj_name(self, obj_or_name):
        obj, name = (self.name_to_obj[obj_or_name], obj_or_name) if type(obj_or_name) == str \
            else (obj_or_name, self.obj_to_name[obj_or_name])
        self.name_to_obj.pop(name)
        self.obj_to_name.pop(obj)

    def check_name(self, name):
        return not(name in self.name_to_obj)

    @property
    def name_to_obj(self) -> dict[str, Any]:
        return copy(self._name_to_obj)

    @property
    def obj_to_name(self) -> dict[Any, str]:
        return copy(self._obj_to_name)


GNOM = GlobalNameObjectMapping()


class NameDescriptor:

    def __init__(self, start_index=1):
        assert type(start_index) == int, 'Start index must be int'
        self.start_index = start_index

    def __get__(self, instance, owner=None):

        if not (instance is None) and not hasattr(instance, '_name'):
            instance._name = None

        if instance is None:
            return owner.__name__
        else:
            if not (instance._name is None):
                return instance._name
            else:
                i = self.start_index
                while True:
                    if i < 1:
                        name_candidate = '{}_{}'.format(owner.__name__, '0'*(1-i))
                    else:
                        name_candidate = '{}_{}'.format(owner.__name__, i)
                    if GNOM.check_name(name_candidate):
                        instance._name = name_candidate
                        GNOM.register_obj_name(instance, name_candidate)
                        return name_candidate
                    else:
                        i += 1

    def __set__(self, instance, name_candidate):
        prefix = instance.__class__.__name__ + '_'
        assert type(name_candidate) == str, 'Name need be str'
        assert bool(re.fullmatch(r'\w+', name_candidate)), 'Name have to consists of alphas, nums and _'
        assert name_candidate.startswith(prefix), 'Name have to begin from className_'
        assert name_candidate != prefix, 'name cannot be == prefix; add specification to end'
        assert not name_candidate[
                   len(prefix):].isdigit(), 'Not auto-name cannot be (prefix + int); choose other name'
        assert GNOM.check_name(name_candidate), 'Name {} already exists'.format(name_candidate)
        if hasattr(instance, '_name'):
            GNOM.remove_obj_name(instance)
        instance._name = name_candidate
        GNOM.register_obj_name(instance, name_candidate)


def check_all_nodes_associated(graph_template_: BasePolarGraph):
    for node in graph_template_.not_inf_nodes:
        assert node in graph_template_.am.cells, 'Node {} is not associated'.format(node)


def get_splitter_nodes_cells(graph_template_: BasePolarGraph) -> set[tuple[PolarNode, TypedCell]]:
    values = set()
    for node in graph_template_.not_inf_nodes:
        cell = graph_template_.am.cells[node]['attrib_node']
        req_type = cell.required_type
        cls = get_class_by_str(req_type, True)
        if issubclass(cls, BoundedStringSet):
            values.add((node, cell))
    return values


def expand_splitters(graph_template_: BasePolarGraph):
    for node, cell in get_splitter_nodes_cells(graph_template_):
        cls = get_class_by_str(cell.required_type, True)
        unique_values: list = cls.unique_values
        need_count_of_links = len(unique_values)
        existing_count_of_links = len(node.ni_nd.links)
        if need_count_of_links == existing_count_of_links:
            continue
        assert existing_count_of_links == 1, 'Found situation not fully expanded splitter with <> 1 count links'
        link = node.ni_nd.links.pop()
        for _ in range(need_count_of_links - existing_count_of_links):
            graph_template_.connect_nodes(*link.ni_s)
        for link_ in node.ni_nd.links:
            move_ = node.ni_nd.get_move(link_)
            graph_template_.am.create_cell(move_, unique_values.pop())


def init_switch_splitters(graph_template_: BasePolarGraph):
    for node, cell in get_splitter_nodes_cells(graph_template_):
        if not (cell.candidate_value is None):
            cell.evaluate()
            found_move = graph_template_.am.get_single_elm_by_cell_content(PGMove, cell.value, node.ni_nd.moves)
            node.ni_nd.choice_move_activate(found_move)


class AttribGraphTemplatesDescriptor:

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if hasattr(instance, '_graph_template'):
            return instance._graph_template

        g_t = BasePolarGraph()
        a_m = g_t.am
        a_m.node_assoc_class = AttribNodeAssociation
        a_m.move_assoc_class = AttribMoveAssociation
        a_m.auto_set_curr_context()

        if owner == CoordSystem:
            node_rel_cs, _, _ = g_t.insert_node_single_link()
            node_check_dependence, _, _ = g_t.insert_node_single_link(node_rel_cs.ni_nd)
            node_x, link_up_x, _ = g_t.insert_node_single_link(node_check_dependence.ni_nd)
            move_to_x = node_check_dependence.ni_nd.get_move(link_up_x)
            node_y, _, _ = g_t.insert_node_single_link(node_x.ni_nd)
            node_alpha, link_up_alpha, _ = g_t.insert_node_single_link(node_check_dependence.ni_nd)
            move_to_alpha = node_check_dependence.ni_nd.get_move(link_up_alpha)
            node_connect_polarity, _, _ = g_t.insert_node_single_link(node_alpha.ni_nd)
            node_co_x = g_t.insert_node_neck(g_t.inf_node_nd.ni_pu)
            node_co_y = g_t.insert_node_neck(g_t.inf_node_nd.ni_pu)

            a_m.create_cell(node_rel_cs, 'cs_relative_to', 'CoordSystem')
            a_m.create_cell(node_check_dependence, 'dependence', 'BSSDependency', BSSDependency('dependent'))
            a_m.create_cell(node_x, 'x', 'int')
            a_m.create_cell(move_to_x, 'dependent')
            a_m.create_cell(node_y, 'y', 'int')
            a_m.create_cell(node_alpha, 'alpha', 'int')
            a_m.create_cell(move_to_alpha, 'independent')
            a_m.create_cell(node_connect_polarity, 'connection_polarity', 'End', End('negative_down'))
            a_m.create_cell(node_co_x, 'co_x', 'BSSBool', BSSBool('True'))
            a_m.create_cell(node_co_y, 'co_y', 'BSSBool', BSSBool('True'))

        check_all_nodes_associated(g_t)
        expand_splitters(g_t)
        init_switch_splitters(g_t)

        instance._graph_template = g_t
        return g_t

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class AttribDescriptor:

    def __get__(self, instance, owner=None) -> Union[list[AttributeFormat], AttribDescriptor]:
        if instance is None:
            return self
        g_t = instance.graph_template
        route_from_to_: PGRoute = g_t.free_roll(g_t.inf_node_pu.ni_nd)
        route_result_ = g_t.am.extract_route_content(route_from_to_)
        formatted_result: list[AttributeFormat] = []
        splitter_cells_set = {i[1] for i in get_splitter_nodes_cells(g_t)}
        for i, set_cells in enumerate(route_result_):
            if not set_cells:
                continue
            cell = set_cells.pop()
            if cell not in splitter_cells_set:
                if issubclass(type(cell), TypedCell):
                    # print('here for ',cell.name)
                    af = AttributeFormat(BSSAttributeType('value'), cell.name, cell.candidate_value)
                else:
                    af = AttributeFormat(BSSAttributeType('title'), cell.name)
            else:
                str_value = route_result_[i + 1].pop().name
                cls = get_class_by_str(cell.required_type)
                af = AttributeFormat(BSSAttributeType('splitter'), cell.name, str_value, cls.unique_values)
            if issubclass(type(cell), TypedCell):
                if cell.candidate_value is None:
                    af.check_success = True
                else:
                    af.check_success = cell.check_candidate_value()
            formatted_result.append(af)
        return formatted_result

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class DynamicAttributeControl:
    graph_template = AttribGraphTemplatesDescriptor()
    graph_attr = AttribDescriptor()
    name = NameDescriptor()

    def __init__(self):
        pass

    def change_value(self, af: AttributeFormat):
        # print('change val for ', af)
        am = self.graph_template.am
        node = am.get_single_elm_by_cell_content(PolarNode, af.attr_name)
        cell: TypedCell = am.get_elm_cell_by_context(node)
        if str(af.attr_type) in {'splitter', 'value'}:
            # print('chv', af)
            cls = get_class_by_str(cell.required_type, True)
            if af.attr_type == 'splitter':
                move = am.get_single_elm_by_cell_content(PGMove, af.attr_value, node.ni_nd.moves)
                node.ni_nd.choice_move_activate(move)
                cell.candidate_value = cls(af.attr_value)
            if af.attr_type == 'value':
                # print('set cand val for ', af.attr_value)
                cell.candidate_value = af.attr_value

    def check_values_types(self):
        pass

    def create_object(self):
        pass


class CoordSystem(DynamicAttributeControl):
    pass


class Line(DynamicAttributeControl):
    pass

    # def __init__(self):
    #     super().__init__()


if __name__ == '__main__':

    test = 'test_1'
    if test == 'test_1':
        pass
    GCS = CoordSystem()
    GCS_2 = CoordSystem()
    ln_1 = Line()
    ln_2 = Line()
    ln_2.name = 'Line_2d'
    ln_3 = Line()
    # print(GCS.graph_template)
    # free_route = GCS.graph_template.free_roll(GCS.graph_template.inf_node_pu.ni_nd)
    # cont_s = GCS.graph_template.am.extract_route_content(free_route)
    # for cont in cont_s:
    #     print(cont.pop().name)
    # print(GCS.graph_template is GCS_2.graph_template)

    # print(GCS.graph_attr)
    # for attr in GCS.graph_attr:
    #     print(attr)
    # attr_cs = GCS.graph_attr[0]
    # attr_cs.attr_value = GCS_2
    # attr_form_dep = GCS.graph_attr[1]
    # attr_form_dep.attr_value = 'independent'
    # attr_form_cox = GCS.graph_attr[5]
    # attr_form_cox.attr_value = 'False'

    # GCS.change_value(attr_cs)
    # GCS.change_value(attr_form_dep)
    # GCS.change_value(attr_form_cox)
    # print()
    # for attr in GCS.graph_attr:
    #     print(attr)

    # GNOM.register_obj_name(123, 'Cyfer')
    # GNOM.register_obj_name(1234, 'Cyfe')
    # print(GNOM.name_to_obj)
    # print(GNOM.obj_to_name)

    print(GCS.name)
    print(CoordSystem.name)

    print(ln_1.name)
    print(ln_2.name)
    print(ln_3.name)
