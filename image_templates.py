from __future__ import annotations

from nv_associations import *
from nv_cell import AttribCell, BSSAttribCellType
from nv_polar_graph import (BasePolarGraph,
                            # End,
                            # PolarNode,
                            PGMove,
                            # PGRoute,
                            # GraphStateSaver
                            )


def expand_splitters(graph_template_: BasePolarGraph):
    for node, cell in get_splitter_nodes_cells(graph_template_):
        cls = get_class_by_str(cell.str_req, True)
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
            unique_value = unique_values.pop()
            graph_template_.am.bind_cell(move_, AttribCell(unique_value))


def init_splitter_move_activation(graph_template_: BasePolarGraph):
    am = graph_template_.am
    for node, cell in get_splitter_nodes_cells(graph_template_):
        if cell.str_value:
            move_for_init_active = am.get_single_elm_by_cell_content(PGMove, cell.str_value, node.ni_nd.moves)
            node.ni_nd.choice_move_activate(move_for_init_active)


class AttribBuildGraphTemplateDescriptor:

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if hasattr(instance, '_graph_build_template'):
            return instance._graph_build_template

        g_b_t = BasePolarGraph()
        a_m = g_b_t.am
        a_m.node_assoc_class = AttribNodeAssociation
        a_m.move_assoc_class = AttribMoveAssociation
        a_m.auto_set_curr_context()

        if owner == CoordinateSystem:
            node_rel_cs, _, _ = g_b_t.insert_node_single_link()
            node_check_dependence, _, _ = g_b_t.insert_node_single_link(node_rel_cs.ni_nd)
            node_x, link_up_x, _ = g_b_t.insert_node_single_link(node_check_dependence.ni_nd)
            move_to_x = node_check_dependence.ni_nd.get_move(link_up_x)
            node_y, _, _ = g_b_t.insert_node_single_link(node_x.ni_nd)
            node_alpha, link_up_alpha, _ = g_b_t.insert_node_single_link(node_check_dependence.ni_nd)
            move_to_alpha = node_check_dependence.ni_nd.get_move(link_up_alpha)
            node_connect_polarity, _, _ = g_b_t.insert_node_single_link(node_alpha.ni_nd)
            node_co_x = g_b_t.insert_node_neck(g_b_t.inf_node_nd.ni_pu)
            node_co_y = g_b_t.insert_node_neck(g_b_t.inf_node_nd.ni_pu)

            a_m.bind_cell(node_rel_cs, AttribCell('cs_relative_to', 'CoordinateSystem'))
            a_m.bind_cell(node_check_dependence,
                          AttribCell('dependence', 'BSSDependency', 'independent', BSSAttribCellType('common_splitter')))
            a_m.bind_cell(node_x, AttribCell('x', 'int'))
            a_m.bind_cell(move_to_x, AttribCell('dependent'))
            a_m.bind_cell(node_y, AttribCell('y', 'int'))
            a_m.bind_cell(node_alpha, AttribCell('alpha', 'int'))
            a_m.bind_cell(move_to_alpha, AttribCell('independent'))
            a_m.bind_cell(node_connect_polarity,
                          AttribCell('connection_polarity', 'End', 'negative_down', BSSAttribCellType('common_splitter')))
            a_m.bind_cell(node_co_x, AttribCell('co_x', 'BSSBool', 'True', BSSAttribCellType('bool_splitter')))
            a_m.bind_cell(node_co_y, AttribCell('co_y', 'BSSBool', 'True', BSSAttribCellType('bool_splitter')))

        if owner == GroundLine:
            node_rel_cs, _, _ = g_b_t.insert_node_single_link()
            node_translate_or_rotate, _, _ = g_b_t.insert_node_single_link(node_rel_cs.ni_nd)
            node_y, link_up_translate, _ = g_b_t.insert_node_single_link(node_translate_or_rotate.ni_nd)
            move_to_translate = node_translate_or_rotate.ni_nd.get_move(link_up_translate)
            node_center_point, link_up_rotate, _ = g_b_t.insert_node_single_link(node_translate_or_rotate.ni_nd)
            move_to_rotate = node_translate_or_rotate.ni_nd.get_move(link_up_rotate)
            node_alpha, _, _ = g_b_t.insert_node_single_link(node_center_point.ni_nd)

            a_m.bind_cell(node_rel_cs, AttribCell('cs_relative_to', 'CoordinateSystem'))
            a_m.bind_cell(node_translate_or_rotate,
                          AttribCell('move_method', 'BSSMoveMethod', 'translational', BSSAttribCellType('common_splitter')))
            a_m.bind_cell(move_to_translate, AttribCell('translational'))
            a_m.bind_cell(move_to_rotate, AttribCell('rotational'))
            a_m.bind_cell(node_y, AttribCell('y', 'int'))
            a_m.bind_cell(node_center_point, AttribCell('center_point', 'Point'))
            a_m.bind_cell(node_alpha, AttribCell('alpha', 'int'))

        if owner == Point:
            node_rel_cs, _, _ = g_b_t.insert_node_single_link()
            node_x, _, _ = g_b_t.insert_node_single_link(node_rel_cs.ni_nd)
            node_gl_or_line, _, _ = g_b_t.insert_node_single_link(node_x.ni_nd)
            node_gl, link_gl, _ = g_b_t.insert_node_single_link(node_gl_or_line.ni_nd)
            move_to_gl = node_gl_or_line.ni_nd.get_move(link_gl)
            node_line, link_line, _ = g_b_t.insert_node_single_link(node_gl_or_line.ni_nd)
            move_to_line = node_gl_or_line.ni_nd.get_move(link_line)

            a_m.bind_cell(node_rel_cs, AttribCell('cs_relative_to', 'CoordinateSystem'))
            a_m.bind_cell(node_x, AttribCell('x', 'int'))
            a_m.bind_cell(node_gl_or_line,
                          AttribCell('on_line_or_ground_line', 'BSSGroundLineOrLine',
                               'ground_line', BSSAttribCellType('common_splitter')))
            a_m.bind_cell(move_to_gl, AttribCell('ground_line'))
            a_m.bind_cell(move_to_line, AttribCell('line'))
            a_m.bind_cell(node_gl, AttribCell('ground_line', 'GroundLine'))
            a_m.bind_cell(node_line, AttribCell('line', 'Line'))

        if owner == Line:
            node_first_point, _, _ = g_b_t.insert_node_single_link()
            node_second_point, _, _ = g_b_t.insert_node_single_link(node_first_point.ni_nd)

            a_m.bind_cell(node_first_point, AttribCell('first_point', 'Point'))
            a_m.bind_cell(node_second_point, AttribCell('second_point', 'Point'))

        expand_splitters(g_b_t)
        instance._graph_build_template = g_b_t
        return g_b_t

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class AttribCommonGraphTemplateDescriptor:

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

        node_name_title, _, _ = g_t.insert_node_single_link()
        node_name, _, _ = g_t.insert_node_single_link(node_name_title.ni_nd)
        node_build_title, _, _ = g_t.insert_node_single_link(node_name.ni_nd)
        node_evaluate_title, _, _ = g_t.insert_node_single_link(node_build_title.ni_nd)
        node_view_title, _, _ = g_t.insert_node_single_link(node_evaluate_title.ni_nd)

        a_m.bind_cell(node_name_title, AttribCell('Name options'))
        a_m.bind_cell(node_name, AttribCell('name', owner.__name__, cell_type=BSSAttribCellType('name')))
        a_m.bind_cell(node_build_title, AttribCell('Build options'))
        a_m.bind_cell(node_evaluate_title, AttribCell('Evaluation options'))
        a_m.bind_cell(node_view_title, AttribCell('View options'))

        gbt = instance.graph_build_template
        g_t.aggregate(gbt, node_build_title.ni_nd, node_evaluate_title.ni_pu)

        init_splitter_move_activation(g_t)
        instance._graph_template = g_t
        return g_t

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class AttrControlObject:
    graph_build_template = AttribBuildGraphTemplateDescriptor()
    graph_template = AttribCommonGraphTemplateDescriptor()

    def __init__(self):
        pass
        # self.pick_status = BSSPickObjectStatus('p_default')
        # self.corrupt_status = BSSCorruptObjectStatus('c_default')


class CoordinateSystem(AttrControlObject):
    pass


class Point(AttrControlObject):
    pass


class Line(AttrControlObject):
    pass


class GroundLine(AttrControlObject):
    pass