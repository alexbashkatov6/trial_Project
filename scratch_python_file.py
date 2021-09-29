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
from nv_typed_cell import TypedCell
from copy import deepcopy

BSSDependency = bounded_string_set('BSSDependency', [['dependent'], ['independent']])
BSSBool = bounded_string_set('BSSBool', [['True'], ['False']])


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
            a_m.create_cell(node_rel_cs, 'cs_relative_to', 'CoordSystem')
            node_check_dependence, _, _ = g_t.insert_node_single_link(node_rel_cs.ni_nd)
            a_m.create_cell(node_check_dependence, 'dependence', 'BSSDependency', BSSDependency('dependent'))
            node_x, link_up_x, _ = g_t.insert_node_single_link(node_check_dependence.ni_nd)
            a_m.create_cell(node_x, 'x', 'int')
            move_to_x = node_check_dependence.ni_nd.get_move(link_up_x)
            a_m.create_cell(move_to_x, 'dependent', 'str')
            node_y, _, _ = g_t.insert_node_single_link(node_x.ni_nd)
            a_m.create_cell(node_y, 'y', 'int')
            node_alpha, link_up_alpha, _ = g_t.insert_node_single_link(node_check_dependence.ni_nd)
            a_m.create_cell(node_alpha, 'alpha', 'int')
            move_to_alpha = node_check_dependence.ni_nd.get_move(link_up_alpha)
            a_m.create_cell(move_to_alpha, 'independent', 'str')
            node_connect_polarity, _, _ = g_t.insert_node_single_link(node_alpha.ni_nd)
            a_m.create_cell(node_connect_polarity, 'connection_polarity', 'End', End('negative_down'))
            node_co_x = g_t.insert_node_neck(g_t.inf_node_nd.ni_pu)
            a_m.create_cell(node_co_x, 'co_x', 'BSSBool', BSSBool('True'))
            node_co_y = g_t.insert_node_neck(g_t.inf_node_nd.ni_pu)
            a_m.create_cell(node_co_y, 'co_y', 'BSSBool', BSSBool('True'))

        self.check_all_nodes_associated(g_t)
        self.expand_splitters(g_t)
        self.switch_splitters(g_t)

        instance._graph_template = g_t
        return g_t

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))

    @staticmethod
    def check_all_nodes_associated(graph_template_: BasePolarGraph):
        for node in graph_template_.not_inf_nodes:
            assert node in graph_template_.am.cells, 'Node {} is not associated'.format(node)

    @staticmethod
    def get_splitter_nodes_cells(graph_template_: BasePolarGraph) -> set[tuple[PolarNode, TypedCell]]:
        values = set()
        for node in graph_template_.not_inf_nodes:
            cell = graph_template_.am.cells[node]['attrib_node']
            req_type = cell.required_type
            cls = get_class_by_str(req_type)
            if issubclass(cls, BoundedStringSet):
                values.add((node, cell))
        return values

    def expand_splitters(self, graph_template_: BasePolarGraph):
        for node, cell in self.get_splitter_nodes_cells(graph_template_):
            cls = get_class_by_str(cell.required_type)
            unique_values: list = cls.unique_values
            need_count_of_links = len(unique_values)
            existing_count_of_links = len(node.ni_nd.links)
            if need_count_of_links == existing_count_of_links:
                continue
            assert existing_count_of_links == 1, 'Found situation not fully expanded splitter with <> 1 count links'
            link = node.ni_nd.links.pop()
            for _ in range(need_count_of_links-existing_count_of_links):
                graph_template_.connect_nodes(*link.ni_s)
            for link_ in node.ni_nd.links:
                move_ = node.ni_nd.get_move(link_)
                graph_template_.am.create_cell(move_, unique_values.pop(), 'str')

    def switch_splitters(self, graph_template_: BasePolarGraph):
        for node, cell in self.get_splitter_nodes_cells(graph_template_):
            cell.evaluate()
            found_move = graph_template_.am.get_single_elm_by_cell_content(PGMove, cell.value, node.ni_nd.moves)
            node.ni_nd.choice_move_activate(found_move)


class AttribDescriptor:
    def __get__(self, instance, owner=None) -> Union[list[AttributeFormat], AttribDescriptor]:
        if instance is None:
            return self
        g_t = instance.graph_template
        route_from_to_: PGRoute = g_t.free_roll(g_t.inf_node_pu.ni_nd)
        route_result_ = g_t.am.extract_route_content({PolarNode: 'attr_tuple', PGMove: 'splitter_value'},
                                                     route_from_to_, get_as_strings=False)
        result: list[AttributeFormat] = []
        for i, element in enumerate(route_result_):
            if not(type(element) == tuple):
                continue
            else:
                name, cls = element
                if cls is None:
                    result.append(AttributeFormat(BSSAttributeType('title'), name))
                elif issubclass(cls, BoundedStringSet):
                    str_value = route_result_[i+1]
                    result.append(AttributeFormat(BSSAttributeType('bss_splitter'), name,
                                                  str_value, cls.unique_values))
                else:
                    result.append(AttributeFormat(BSSAttributeType('value'), name,
                                                  'Wow value'))
        print('route_result', len(route_result_), route_result_)
        return result

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class DynamicAttributeControl:
    graph_template = AttribGraphTemplatesDescriptor()
    graph_attr = AttribDescriptor()

    def __init__(self):
        pass

    def change_value(self):
        pass

    def check_values_types(self):
        pass

    def create_object(self):
        pass


class CoordSystem(DynamicAttributeControl):
    pass

    # def __init__(self):
    #     super().__init__()


if __name__ == '__main__':

    test = 'test_1'
    if test == 'test_1':
        pass
    GCS = CoordSystem()
    GCS_2 = CoordSystem()
    print(GCS.graph_template)
    free_route = GCS.graph_template.free_roll(GCS.graph_template.inf_node_pu.ni_nd)
    cont_s = GCS.graph_template.am.extract_route_content(free_route)
    for cont in cont_s:
        print(cont.pop().name)
    print(GCS.graph_template is GCS_2.graph_template)
