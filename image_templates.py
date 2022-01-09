from __future__ import annotations
from typing import Union

from image_attribute import ImageAttribute, TitleAttribute, SplitterAttribute, VirtualSplitterAttribute, FormAttribute
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Move
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


def auto_expand_splitters(graph: OneComponentTwoSidedPG):
    nodes_splitters = splitter_nodes(graph)
    for nodes_splitter in nodes_splitters:
        node, splitter = nodes_splitter
        count_links_needed = len(splitter.possible_values)
        count_links_current = len(node.ni_nd.links)
        if count_links_current < count_links_needed:
            assert count_links_current == 1, "More then 1 link in auto splitter"
            link = node.ni_nd.links[0]
            for _ in range(count_links_needed-count_links_current):
                graph.connect(*link.ni_s)
            for i, move in enumerate(node.ni_nd.moves):
                move.append_cell_obj(SplitterMove(i))


def move_by_int(node: PolarNode, value: int) -> Move:
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


class TemplateDescriptor:

    def __get__(self, instance, owner):
        if not hasattr(owner, "_template"):
            g = COMMON_TEMPLATE.copy_part()
            name = g.insert_node(g.node_copy_mapping[name_options].ni_nd, g.node_copy_mapping[build_options].ni_pu)
            name.append_cell_obj(FormAttribute("name", "{}_name".format(owner.__name__)))
            ni_pu_eval_opt = g.node_copy_mapping[evaluate_options].ni_pu

            if owner == CoordinateSystem:
                rel_cs = g.insert_node(g.node_copy_mapping[build_options].ni_nd, ni_pu_eval_opt)
                rel_cs.append_cell_obj(FormAttribute('cs_relative_to', 'CoordinateSystem'))
                dep = g.insert_node(rel_cs.ni_nd, ni_pu_eval_opt)
                dep.append_cell_obj(SplitterAttribute('dependence', CEDependence(CEDependence.dependent)))
                x = g.insert_node(dep.ni_nd, ni_pu_eval_opt)
                move_x = dep.ni_nd.get_move_by_link(x.ni_pu.links[0])
                x.append_cell_obj(FormAttribute('x', 'int'))
                move_x.append_cell_obj(SplitterMove(CEDependence.dependent))
                y = g.insert_node(x.ni_nd, ni_pu_eval_opt)
                y.append_cell_obj(FormAttribute('y', 'int'))
                alpha = g.insert_node(dep.ni_nd, ni_pu_eval_opt)
                move_alpha = dep.ni_nd.get_move_by_link(alpha.ni_pu.links[0])
                alpha.append_cell_obj(FormAttribute('alpha', 'int'))
                move_alpha.append_cell_obj(SplitterMove(CEDependence.independent))
                node_co_x = g.insert_node_neck(ni_pu_eval_opt)
                node_co_x.append_cell_obj(SplitterAttribute('co_x', CEBool(CEBool.true)))
                node_co_y = g.insert_node_neck(ni_pu_eval_opt)
                node_co_y.append_cell_obj(SplitterAttribute('co_y', CEBool(CEBool.true)))

            if owner == Axis:
                rel_cs = g.insert_node(g.node_copy_mapping[build_options].ni_nd, ni_pu_eval_opt)
                rel_cs.append_cell_obj(FormAttribute('cs_relative_to', 'CoordinateSystem'))
                cr_m = g.insert_node(rel_cs.ni_nd, ni_pu_eval_opt)
                cr_m.append_cell_obj(SplitterAttribute('move_method',
                                                       CEAxisCreationMethod(CEAxisCreationMethod.translational)))
                y = g.insert_node(cr_m.ni_nd, ni_pu_eval_opt)
                move_y = cr_m.ni_nd.get_move_by_link(y.ni_pu.links[0])
                y.append_cell_obj(FormAttribute('y', 'int'))
                move_y.append_cell_obj(SplitterMove(CEAxisCreationMethod.translational))
                pnt = g.insert_node(cr_m.ni_nd, ni_pu_eval_opt)
                move_pnt = cr_m.ni_nd.get_move_by_link(pnt.ni_pu.links[0])
                pnt.append_cell_obj(FormAttribute('center_point', 'Point'))
                move_pnt.append_cell_obj(SplitterMove(CEAxisCreationMethod.rotational))
                alpha = g.insert_node(pnt.ni_nd, ni_pu_eval_opt)
                alpha.append_cell_obj(FormAttribute('alpha', 'int'))

            if owner == Point:
                rel_cs = g.insert_node(g.node_copy_mapping[build_options].ni_nd, ni_pu_eval_opt)
                rel_cs.append_cell_obj(FormAttribute('cs_relative_to', 'CoordinateSystem'))
                x = g.insert_node(rel_cs.ni_nd, ni_pu_eval_opt)
                x.append_cell_obj(FormAttribute('x', 'int'))
                cr_m = g.insert_node(x.ni_nd, ni_pu_eval_opt)
                cr_m.append_cell_obj(SplitterAttribute('on_axis_or_line',
                                                       CEAxisOrLine(CEAxisOrLine.axis)))
                axis = g.insert_node(cr_m.ni_nd, ni_pu_eval_opt)
                move_axis = cr_m.ni_nd.get_move_by_link(axis.ni_pu.links[0])
                axis.append_cell_obj(FormAttribute('axis', 'Axis'))
                move_axis.append_cell_obj(SplitterMove(CEAxisOrLine.axis))
                line = g.insert_node(cr_m.ni_nd, ni_pu_eval_opt)
                move_line = cr_m.ni_nd.get_move_by_link(line.ni_pu.links[0])
                line.append_cell_obj(FormAttribute('line', 'Line'))
                move_line.append_cell_obj(SplitterMove(CEAxisOrLine.line))

            if owner == Line:
                pnt_1 = g.insert_node(g.node_copy_mapping[build_options].ni_nd, ni_pu_eval_opt)
                pnt_1.append_cell_obj(FormAttribute('first_point', 'Point'))
                pnt_2 = g.insert_node(pnt_1.ni_nd, ni_pu_eval_opt)
                pnt_2.append_cell_obj(FormAttribute('second_point', 'Point'))

            auto_expand_splitters(g)
            splitter_moves_activation(g)
            owner._template = g
        if not hasattr(instance, "_template_"):
            instance._template_ = owner._template.copy_part()
        return instance._template_

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class ImageObject:
    template = TemplateDescriptor()

    def get_attributes(self) -> list[ImageAttribute]:
        return [node.cell_objs[0] for node in self.template.free_roll().nodes if node.cell_objs]

    def switch_splitter(self, splitter_name: str, new_str_or_bool: Union[str, bool], virtual: bool = False):
        node_splitters = splitter_nodes(self.template, virtual)
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


if __name__ == "__main__":
    # print(len(COMMON_TEMPLATE.nodes))
    cs = CoordinateSystem()  # CoordinateSystem Axis Point Line
    tmpl = cs.template
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
    cs.switch_splitter("dependence", "independent")
    print([attrib.name for attrib in cs.get_attributes()])
    cs.switch_splitter("dependence", "dependent")
    print([attrib.name for attrib in cs.get_attributes()])
