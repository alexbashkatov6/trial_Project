from __future__ import annotations
from typing import Union

from image_attribute import ImageAttribute, TitleAttribute, SplitterAttribute, VirtualSplitterAttribute, FormAttribute
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Move, NodesMerge
from custom_enum import CustomEnum
from cell_object import CellObject

COMMON_TEMPLATE = OneComponentTwoSidedPG()

name_options = COMMON_TEMPLATE.insert_node()
name_options.append_cell_obj(TitleAttribute("Name options"))
build_options = COMMON_TEMPLATE.insert_node(name_options.ni_nd)
build_options.append_cell_obj(TitleAttribute("Build options"))
evaluate_options = COMMON_TEMPLATE.insert_node(build_options.ni_nd)
evaluate_options.append_cell_obj(TitleAttribute("Evaluation options"))
view_options = COMMON_TEMPLATE.insert_node(evaluate_options.ni_nd)
view_options.append_cell_obj(TitleAttribute("View options"))


class SplitterMove(CellObject):
    def __init__(self, int_value: int):
        super().__init__()
        self._int_value = int_value

    @property
    def int_value(self):
        return self._int_value


class CEDependence(CustomEnum):
    dependent = 0
    independent = 1


class CEBool(CustomEnum):
    false = 0
    true = 1


class CEAxisCreationMethod(CustomEnum):
    translational = 0
    rotational = 1


class CEAxisOrLine(CustomEnum):
    axis = 0
    line = 1


class CELightType(CustomEnum):
    train = 0
    shunt = 1


class CELightColor(CustomEnum):
    red = 0
    blue = 1
    white = 2
    yellow = 3
    green = 4


class CEBorderType(CustomEnum):
    standoff = 0
    ab = 1
    pab = 2


def splitter_nodes(graph: OneComponentTwoSidedPG, virtual: bool = False) \
        -> set[tuple[PolarNode, Union[SplitterAttribute, VirtualSplitterAttribute]]]:
    nodes_splitters = set()
    for node in graph.nodes:
        if node.cell_objs:
            co = node.cell_objs[0]
            if virtual:
                if isinstance(co, VirtualSplitterAttribute):
                    nodes_splitters.add((node, co))
            else:
                if isinstance(co, SplitterAttribute):
                    nodes_splitters.add((node, co))
    return nodes_splitters


# def auto_expand_splitters(graph: OneComponentTwoSidedPG):
#     nodes_splitters = splitter_nodes(graph)
#     for nodes_splitter in nodes_splitters:
#         node, splitter = nodes_splitter
#         count_links_needed = len(splitter.possible_values)
#         count_links_current = len(node.ni_nd.links)
#         if count_links_current < count_links_needed:
#             assert count_links_current == 1, "More then 1 link in auto splitter"
#             link = node.ni_nd.links[0]
#             for _ in range(count_links_needed-count_links_current):
#                 graph.connect(*link.ni_s)
#             for i, move in enumerate(node.ni_nd.moves):
#                 move.append_cell_obj(SplitterMove(i))


def move_by_int(node: PolarNode, value: int) -> Move:
    moves = node.ni_nd.moves
    if len(moves) == 1:
        return moves[0]
    for move in node.ni_nd.moves:
        if value == move.cell_objs[0].int_value:
            return move
    assert False, "Not found"


def splitter_moves_activation(graph: OneComponentTwoSidedPG):
    nodes_splitters = splitter_nodes(graph)
    for nodes_splitter in nodes_splitters:
        node, splitter = nodes_splitter
        move = move_by_int(node, splitter.current_value)
        node.ni_nd.choice_move_activate(move)


class CommonTemplateDescriptor:
    def __get__(self, instance, owner):
        if not hasattr(owner, "_common_template"):
            owner._common_template = COMMON_TEMPLATE.copy_part()
        if not hasattr(instance, "_i_common_template"):
            instance._i_common_template = owner._common_template
        g = instance._i_common_template
        build_t: OneComponentTwoSidedPG = instance.build_template
        name_t: OneComponentTwoSidedPG = instance.name_template
        g.aggregate(name_t, [NodesMerge(g.node_copy_mapping[name_options].ni_nd, name_t.inf_pu.ni_pu),
                             NodesMerge(g.node_copy_mapping[build_options].ni_pu, name_t.inf_nd.ni_nd)])
        g.aggregate(build_t, [NodesMerge(g.node_copy_mapping[build_options].ni_nd, build_t.inf_pu.ni_pu),
                              NodesMerge(g.node_copy_mapping[evaluate_options].ni_pu, build_t.inf_nd.ni_nd)])
        return instance._i_common_template

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class NameTemplateDescriptor:

    def __get__(self, instance, owner):
        if not hasattr(owner, "_name_template"):
            g = OneComponentTwoSidedPG()
            name = g.insert_node()
            name.append_cell_obj(FormAttribute("name", "{}_name".format(owner.__name__)))
            owner._name_template = g
        if not hasattr(instance, "_i_name_template"):
            instance._i_name_template = owner._name_template.copy_part()
        return instance._i_name_template

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class BuildTemplateDescriptor:

    def __get__(self, instance, owner):
        if not hasattr(owner, "_build_template"):
            g = OneComponentTwoSidedPG()

            if owner == CoordinateSystem:
                rel_cs = g.insert_node()
                rel_cs.append_cell_obj(FormAttribute('cs_relative_to', 'CoordinateSystem'))
                dep = g.insert_node(rel_cs.ni_nd)
                dep.append_cell_obj(SplitterAttribute('dependence', CEDependence(CEDependence.dependent)))
                x = g.insert_node(dep.ni_nd)
                move_x = dep.ni_nd.get_move_by_link(x.ni_pu.links[0])
                x.append_cell_obj(FormAttribute('x', 'int'))
                move_x.append_cell_obj(SplitterMove(CEDependence.dependent))
                y = g.insert_node(x.ni_nd)
                y.append_cell_obj(FormAttribute('y', 'int'))
                alpha = g.insert_node(dep.ni_nd)
                move_alpha = dep.ni_nd.get_move_by_link(alpha.ni_pu.links[0])
                alpha.append_cell_obj(FormAttribute('alpha', 'int'))
                move_alpha.append_cell_obj(SplitterMove(CEDependence.independent))
                node_co_x = g.insert_node_neck()
                node_co_x.append_cell_obj(SplitterAttribute('co_x', CEBool(CEBool.true)))
                node_co_y = g.insert_node_neck()
                node_co_y.append_cell_obj(SplitterAttribute('co_y', CEBool(CEBool.true)))

            if owner == Axis:
                rel_cs = g.insert_node()
                rel_cs.append_cell_obj(FormAttribute('cs_relative_to', 'CoordinateSystem'))
                cr_m = g.insert_node(rel_cs.ni_nd)
                cr_m.append_cell_obj(SplitterAttribute('move_method',
                                                       CEAxisCreationMethod(CEAxisCreationMethod.translational)))
                y = g.insert_node(cr_m.ni_nd)
                move_y = cr_m.ni_nd.get_move_by_link(y.ni_pu.links[0])
                y.append_cell_obj(FormAttribute('y', 'int'))
                move_y.append_cell_obj(SplitterMove(CEAxisCreationMethod.translational))
                pnt = g.insert_node(cr_m.ni_nd)
                move_pnt = cr_m.ni_nd.get_move_by_link(pnt.ni_pu.links[0])
                pnt.append_cell_obj(FormAttribute('center_point', 'Point'))
                move_pnt.append_cell_obj(SplitterMove(CEAxisCreationMethod.rotational))
                alpha = g.insert_node(pnt.ni_nd)
                alpha.append_cell_obj(FormAttribute('alpha', 'int'))

            if owner == Point:
                cr_m = g.insert_node()
                cr_m.append_cell_obj(SplitterAttribute('on_axis_or_line',
                                                       CEAxisOrLine(CEAxisOrLine.axis)))
                axis = g.insert_node(cr_m.ni_nd)
                move_axis = cr_m.ni_nd.get_move_by_link(axis.ni_pu.links[0])
                axis.append_cell_obj(FormAttribute('axis', 'Axis'))
                move_axis.append_cell_obj(SplitterMove(CEAxisOrLine.axis))
                line = g.insert_node(cr_m.ni_nd)
                move_line = cr_m.ni_nd.get_move_by_link(line.ni_pu.links[0])
                line.append_cell_obj(FormAttribute('line', 'Line'))
                move_line.append_cell_obj(SplitterMove(CEAxisOrLine.line))
                x = g.insert_node_neck()
                x.append_cell_obj(FormAttribute('x', 'int'))

            if owner == Line:
                pnt_1 = g.insert_node()
                pnt_1.append_cell_obj(FormAttribute('first_point', 'Point'))
                pnt_2 = g.insert_node(pnt_1.ni_nd)
                pnt_2.append_cell_obj(FormAttribute('second_point', 'Point'))

            if owner == Light:
                l_type = g.insert_node()
                l_type.append_cell_obj(SplitterAttribute('type', CELightType(CELightType.train)))
                pnt = g.insert_node(l_type.ni_nd)
                pnt.append_cell_obj(FormAttribute('point', 'Point'))
                dir_pnt = g.insert_node(pnt.ni_nd)
                dir_pnt.append_cell_obj(FormAttribute('direction_point', 'Point'))
                l_color = g.insert_node(dir_pnt.ni_nd)
                l_color.append_cell_obj(SplitterAttribute('color', CELightColor(CELightColor.red)))

            if owner == RailPoint:
                pnt = g.insert_node()
                pnt.append_cell_obj(FormAttribute('center_point', 'Point'))
                pnt_plus = g.insert_node(pnt.ni_nd)
                pnt_plus.append_cell_obj(FormAttribute('direction_plus_point', 'Point'))
                pnt_minus = g.insert_node(pnt_plus.ni_nd)
                pnt_minus.append_cell_obj(FormAttribute('direction_minus_point', 'Point'))

            if owner == Border:
                b_type = g.insert_node()
                b_type.append_cell_obj(SplitterAttribute('type', CEBorderType(CEBorderType.standoff)))

            if owner == Section:
                pnt = g.insert_node()
                pnt.append_cell_obj(FormAttribute('point', 'Point'))

            # auto_expand_splitters(g)
            splitter_moves_activation(g)
            owner._build_template = g
        if not hasattr(instance, "_i_build_template"):
            instance._i_build_template = owner._build_template.copy_part()
        return instance._i_build_template

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class ImageObject:
    common_template: OneComponentTwoSidedPG = CommonTemplateDescriptor()
    build_template: OneComponentTwoSidedPG = BuildTemplateDescriptor()
    name_template: OneComponentTwoSidedPG = NameTemplateDescriptor()

    def get_attributes(self) -> list[ImageAttribute]:
        return [node.cell_objs[0] for node in self.common_template.free_roll().nodes if node.cell_objs]

    def switch_splitter(self, splitter_name: str, new_str_or_bool: Union[str, bool], virtual: bool = False):
        node_splitters = splitter_nodes(self.common_template, virtual)
        found = False
        for node_splitter in node_splitters:
            node, splitter = node_splitter
            if splitter.name == splitter_name:
                found = True
                if virtual:
                    splitter.active = new_str_or_bool
                    move = move_by_int(node, splitter.active)
                else:
                    splitter.current_text = new_str_or_bool
                    move = move_by_int(node, splitter.current_value)
                node.ni_nd.choice_move_activate(move)
        assert found, "Splitter name not found"


class CoordinateSystem(ImageObject):
    pass


class Axis(ImageObject):
    pass


class Point(ImageObject):
    pass


class Line(ImageObject):
    pass


class Light(ImageObject):
    pass


class RailPoint(ImageObject):
    pass


class Border(ImageObject):
    pass


class Section(ImageObject):
    pass


if __name__ == "__main__":
    # print(len(COMMON_TEMPLATE.nodes))
    cs = CoordinateSystem()  # CoordinateSystem Axis Point Line Light RailPoint Border Section
    tmpl = cs.common_template
    print(len(tmpl.nodes))
    print(len(tmpl.links))
    print(tmpl.nodes)
    print(tmpl.inf_nodes)
    print(tmpl.layered_representation())
    print(tmpl.free_roll().nodes)
    for node_ in tmpl.free_roll().nodes:
        if node_.cell_objs:
            cell = node_.cell_objs[0]
            print(cell.name)
    # cs.switch_splitter("on_axis_or_line", "line")
    # print([attrib.name for attrib in cs.get_attributes()])
    # cs.switch_splitter("on_axis_or_line", "axis")
    # print([attrib.name for attrib in cs.get_attributes()])
