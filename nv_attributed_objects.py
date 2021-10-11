from __future__ import annotations
import re
import time

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from nv_typing import *
from nv_associations import *
from nv_bounded_string_set_class import bounded_string_set, BoundedStringSet
from nv_polar_graph import (End,
                            BasePolarGraph,
                            PolarNode,
                            PGMove,
                            PGRoute)
from nv_attribute_format import BSSAttributeType, AttributeFormat
from nv_cell import Cell, DefaultCellChecker, NameCellChecker, SplitterCellChecker, BoolCellChecker, NameAutoSetter, GNM

BSSDependency = bounded_string_set('BSSDependency', [['dependent'], ['independent']])
BSSBool = bounded_string_set('BSSBool', [['True'], ['False']])


def name_translator_storage_to_interface(input_str: str):
    return input_str.replace('_', ' ').capitalize()


def name_translator_interface_to_storage(input_str: str):
    return input_str.replace(' ', '_').lower()


def get_splitter_nodes_cells(graph_template_: BasePolarGraph) -> set[tuple[PolarNode, Cell]]:
    values = set()
    for node in graph_template_.not_inf_nodes:
        cell = graph_template_.am.cell_dicts[node]['attrib_node']
        req_type = cell.req_class_str
        if req_type is None:
            continue
        cls = get_class_by_str(req_type, True)
        if issubclass(cls, BoundedStringSet):
            values.add((node, cell))
    return values


def expand_splitters(graph_template_: BasePolarGraph):
    for node, cell in get_splitter_nodes_cells(graph_template_):
        cls = get_class_by_str(cell.req_class_str, True)
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
            graph_template_.am.create_cell(move_, unique_value)


def init_splitter_move_activation(graph_template_: BasePolarGraph):
    am = graph_template_.am
    for node, cell in get_splitter_nodes_cells(graph_template_):
        if cell.str_value:
            move_for_init_active = am.get_single_elm_by_cell_content(PGMove, cell.str_value, node.ni_nd.moves)
            node.ni_nd.choice_move_activate(move_for_init_active)


class AttribBuildGraphTemplDescr:

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

            a_m.create_cell(node_rel_cs, 'cs_relative_to', DefaultCellChecker('CoordinateSystem'))
            a_m.create_cell(node_check_dependence, 'dependence', SplitterCellChecker(BSSDependency), 'independent')
            a_m.create_cell(node_x, 'x', DefaultCellChecker('int'))
            a_m.create_cell(move_to_x, 'dependent')
            a_m.create_cell(node_y, 'y', DefaultCellChecker('int'))
            a_m.create_cell(node_alpha, 'alpha', DefaultCellChecker('int'))
            a_m.create_cell(move_to_alpha, 'independent')
            a_m.create_cell(node_connect_polarity, 'connection_polarity', SplitterCellChecker(End), 'negative_down')
            a_m.create_cell(node_co_x, 'co_x', BoolCellChecker(BSSBool), 'True')
            a_m.create_cell(node_co_y, 'co_y', BoolCellChecker(BSSBool), 'True')

        if owner == Point:
            node_rel_cs, _, _ = g_b_t.insert_node_single_link()

            a_m.create_cell(node_rel_cs, 'cs_relative_to', DefaultCellChecker('CoordinateSystem'))

        if owner == Line:
            node_rel_cs, _, _ = g_b_t.insert_node_single_link()

            a_m.create_cell(node_rel_cs, 'cs_relative_to', DefaultCellChecker('CoordinateSystem'))

        if owner == GroundLine:
            node_rel_cs, _, _ = g_b_t.insert_node_single_link()

            a_m.create_cell(node_rel_cs, 'cs_relative_to', DefaultCellChecker('CoordinateSystem'))

        expand_splitters(g_b_t)
        instance._graph_build_template = g_b_t
        return g_b_t

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class AttribCommonGraphTemplDescr:

    def __get__(self, instance, owner=None):
        start_time = time.time()
        if instance is None:
            return self
        if hasattr(instance, '_graph_template'):
            return instance._graph_template

        # print('before g_t = ', time.time()-start_time)
        g_t = BasePolarGraph()
        a_m = g_t.am
        a_m.node_assoc_class = AttribNodeAssociation
        a_m.move_assoc_class = AttribMoveAssociation
        a_m.auto_set_curr_context()

        # print('before node_ = ', time.time()-start_time)
        node_name_title, _, _ = g_t.insert_node_single_link()
        node_name, _, _ = g_t.insert_node_single_link(node_name_title.ni_nd)
        node_build_title, _, _ = g_t.insert_node_single_link(node_name.ni_nd)
        node_evaluate_title, _, _ = g_t.insert_node_single_link(node_build_title.ni_nd)
        node_view_title, _, _ = g_t.insert_node_single_link(node_evaluate_title.ni_nd)

        # print('before a_m = ', time.time()-start_time)
        a_m.create_cell(node_name_title, 'Name options')
        a_m.create_cell(node_name, 'name', NameCellChecker(owner))
        a_m.create_cell(node_build_title, 'Build options')
        a_m.create_cell(node_evaluate_title, 'Evaluation options')
        a_m.create_cell(node_view_title, 'View options')

        # print('before gbt = ', time.time()-start_time)
        gbt = instance.graph_build_template
        # print('before aggregate = ', time.time()-start_time)
        g_t.aggregate(gbt, node_build_title.ni_nd, node_evaluate_title.ni_pu)
        # print('after aggregate = ', time.time()-start_time)

        # print('before init_splitter_move_activation = ', time.time()-start_time)
        init_splitter_move_activation(g_t)
        # print('before _graph_template = ', time.time()-start_time)
        instance._graph_template = g_t
        # print('before return = ', time.time()-start_time)
        return g_t

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class AttrControlObject:

    graph_build_template = AttribBuildGraphTemplDescr()
    graph_template = AttribCommonGraphTemplDescr()


class CoordinateSystem(AttrControlObject):
    pass


class Point(AttrControlObject):
    pass


class Line(AttrControlObject):
    pass


class GroundLine(AttrControlObject):
    pass


class CommonAttributeInterface(QObject):

    send_attrib_list = pyqtSignal(list)
    send_class_str = pyqtSignal(str)
    create_readiness = pyqtSignal(bool)
    default_attrib_list = [AttributeFormat(BSSAttributeType('title'), '<pick object>')]

    def __init__(self):
        super().__init__()
        self._current_object = None
        self._is_new_object = False
        self._create_readiness = False

    @property
    def is_new_object(self) -> bool:
        return self._is_new_object

    @property
    def current_object(self) -> Optional[AttrControlObject]:
        return self._current_object

    @current_object.setter
    def current_object(self, value: AttrControlObject) -> None:
        self._current_object = value
        self.send_class_str.emit(value.__class__.__name__)

    def form_attrib_list(self):
        start_time = time.time()
        af_list: list[AttributeFormat] = []
        curr_obj = self.current_object
        if curr_obj is None:
            self.send_attrib_list.emit(self.default_attrib_list)
            return
        # print('before g dur = ', time.time()-start_time)
        g = curr_obj.graph_template
        # print('before am dur = ', time.time()-start_time)
        am = g.am
        # print('before node cycle dur = ', time.time()-start_time)
        for node in g.not_inf_nodes:
            cells = am.cell_dicts[node].values()
            for cell in cells:
                cell.deactivate()
        # print('before fr dur = ', time.time()-start_time)
        fr = g.free_roll()
        # print('before cells_set_list dur = ', time.time()-start_time)
        cells_set_list = am.extract_route_content(fr)
        # print('before splitter_cells_set dur = ', time.time()-start_time)
        splitter_cells_set = [i[1] for i in get_splitter_nodes_cells(g)]
        # print('before i, set_cells dur = ', time.time()-start_time)
        for i, set_cells in enumerate(cells_set_list):
            if not set_cells:
                continue
            cell = set_cells.pop()
            out_name = name_translator_storage_to_interface(cell.name)
            if cell not in splitter_cells_set:
                if cell.checker is None:
                    af = AttributeFormat(BSSAttributeType('title'), out_name)
                else:
                    af = AttributeFormat(BSSAttributeType('value'), out_name, cell.str_value)
                    cell.activate()
            else:
                str_value = cells_set_list[i + 1].pop().name
                cls = get_class_by_str(cell.checker.req_class_str)
                cell.str_value = str_value
                af = AttributeFormat(BSSAttributeType('splitter'), out_name, cell.str_value, cls.unique_values)
                cell.activate()
            cell.check_value()
            af.status_check = cell.status_check
            af_list.append(af)

        self.send_attrib_list.emit(af_list)
        # print('sum dur = ', time.time()-start_time)
        print(af_list)

    @pyqtSlot(str)
    def change_current_object(self, obj_name: str):
        self.current_object = GNM.name_to_obj(obj_name)
        self._is_new_object = False
        self.form_attrib_list()

    @pyqtSlot(str)
    def create_new_object(self, obj_type: str):
        new_object = eval(obj_type)()
        self.current_object = new_object
        self._is_new_object = True
        self.form_attrib_list()
        self.send_class_str.emit(new_object.__class__.__name__)
        self.check_all_values_defined()

    @pyqtSlot(str, str)
    def slot_change_value(self, name: str, new_value: str):
        name = name_translator_interface_to_storage(name)
        curr_obj = self.current_object
        g = curr_obj.graph_template
        node: PolarNode = g.am.get_single_elm_by_cell_content(PolarNode, name)
        assert node, 'Node not found'
        node_cell: Cell = g.am.get_elm_cell_by_context(node)
        assert node_cell, 'Node cell not found'
        node_cell.str_value = new_value
        if node in [i[0] for i in get_splitter_nodes_cells(g)]:
            move = g.am.get_single_elm_by_cell_content(PGMove, new_value, node.ni_nd.moves)
            assert move, 'Node not found'
            node.ni_nd.choice_move_activate(move)
            self.form_attrib_list()
        node_cell.check_value()
        self.check_all_values_defined()

    def get_active_cells(self) -> set[Cell]:
        curr_obj = self.current_object
        g = curr_obj.graph_template
        return {g.am.get_elm_cell_by_context(node) for node in g.am.get_filter_all_cells(PolarNode)}

    def check_all_values_defined(self) -> bool:
        self._create_readiness = all(not(active_cell.value is None) for active_cell in self.get_active_cells())
        self.create_readiness.emit(self._create_readiness)
        return self._create_readiness

    def create_obj_attributes(self):  # , assertion_about_defined=True
        curr_obj = self.current_object
        for active_cell in self.get_active_cells():
            assert re.fullmatch(r'\w+', active_cell.name), 'Name {} for attr is not possible'.format(active_cell.name)
            setattr(curr_obj, active_cell.name, active_cell.value)

    @pyqtSlot()
    def apply_changes(self):
        if self.check_all_values_defined():
            co = self.current_object
            self.create_obj_attributes()
            GDM.add_new_instance(co)
            GDM.add_to_tree_graph(co)
            GNM.register_obj_name(co, co.name)
        self._is_new_object = False


CAI = CommonAttributeInterface()


class GlobalDataManager:

    def __init__(self):
        self._tree_graph = BasePolarGraph()
        self._dependence_graph = BasePolarGraph()
        self._field_graph = BasePolarGraph()

        self._class_instances: dict[str, set[AttrControlObject]] = {}

        self.init_tree_graph()
        self.init_dependence_graph()

        self._gcs = None
        self.init_field_graph()
        self.init_global_coordinate_system()

    @property
    def class_instances(self):
        return self._class_instances

    @property
    def tree_graph(self):
        return self._tree_graph

    @property
    def dependence_graph(self):
        return self._dependence_graph

    @property
    def field_graph(self):
        return self._field_graph

    def init_tree_graph(self):
        a_m = self.tree_graph.am
        a_m.node_assoc_class = TreeNodeAssociation
        a_m.auto_set_curr_context()

    def init_dependence_graph(self):
        a_m = self.dependence_graph.am
        a_m.node_assoc_class = DependenceNodeAssociation
        a_m.auto_set_curr_context()

    def init_field_graph(self):
        a_m = self.field_graph.am
        a_m.node_assoc_class = FieldNodeAssociation
        a_m.link_assoc_class = FieldLinkAssociation
        a_m.move_assoc_class = FieldMoveAssociation
        a_m.auto_set_curr_context()

    def init_global_coordinate_system(self):
        self._gcs = CoordinateSystem()
        self._gcs.name = 'CoordinateSystem_Global'
        GNM.register_obj_name(self._gcs, 'CoordinateSystem_Global')
        self.add_new_instance(self._gcs)

    @property
    def gcs(self) -> CoordinateSystem:
        return self._gcs

    def add_new_instance(self, obj: AttrControlObject):
        cls_name = obj.__class__.__name__
        if cls_name not in self._class_instances:
            self._class_instances[cls_name] = set()
        self._class_instances[cls_name].add(obj)

    def add_to_tree_graph(self, obj: AttrControlObject):
        tg = self.tree_graph
        a_m = tg.am
        node_class = a_m.get_single_elm_by_cell_content(PolarNode, obj.__class__.__name__)
        if node_class is None:
            node_class, _, _ = tg.insert_node_single_link()
            a_m.create_cell(node_class, obj.__class__.__name__)
        node_obj, _, _ = tg.insert_node_single_link(node_class.ni_nd)
        a_m.create_cell(node_obj, obj.name)


GDM = GlobalDataManager()

if __name__ == '__main__':

    test = 'test_1'
    if test == 'test_1':
        pass
        GCS = CoordinateSystem()
        GCS_2 = CoordinateSystem()
        # print(GCS.name)
        # print(GCS_2.name)
        ln_1 = Line()
        ln_2 = Line()
        # ln_2.name = 'Line_2d'
        ln_3 = Line()

        g_t_1 = GCS.graph_template
        # print(len(g_t_1.nodes))
        # a_m_1 = g_t_1.am
        # route = g_t_1.free_roll()
        # print(len(route.nodes))
        # print('cc = ', a_m_1.curr_context)
        # erc_1 = a_m_1.extract_route_content(route)
        # print(len(erc_1))
        # for rc in erc_1:
        #     print(rc.pop().name)
        #
        # print(get_splitter_nodes_cells(g_t_1))

        # CAI.form_attrib_list()

        # print(nv_cell.GNM.name_to_obj)

        # CAI.current_object = GCS
        # CAI.form_attrib_list()
        # print(GCS.graph_template.am.get_filter_all_cells(PolarNode))
        # CAI.create_obj_attributes(False)
        # print(GCS.__dict__)

        CAI.create_new_object('Line')

        CAI.create_new_object('CoordinateSystem')
        CAI.slot_change_value('dependence', 'dependent')
        CAI.slot_change_value('name', 'CoordinateSystem_5')
        CAI.slot_change_value('x', '2')
        CAI.slot_change_value('y', '6')
        CAI.slot_change_value('cs_relative_to', 'CoordinateSystem_Global')

        print(CAI.check_all_values_defined())
        CAI.apply_changes()
        print(GNM.name_to_obj)
        print(GDM.class_instances)
        print(GDM.tree_graph.nodes)

        # g_t_2 = GCS.graph_build_template
        # a_m_2 = g_t_2.am
        # route = g_t_2.free_roll()
        # erc_2 = a_m_2.extract_route_content(route)
        # for rc in erc_2:
        #     print(rc.pop().name)
        # print(len(g_t_2.inf_node_pu.ni_nd.links))
        # print(len(g_t_2.inf_node_nd.ni_pu.links))

        # print(a_m_1.cell_dicts)
        # print(route.moves)

        # free_route = GCS.graph_template.free_roll(GCS.graph_template.inf_node_pu.ni_nd)
        # cont_s = GCS.graph_template.am.extract_route_content(free_route)
        # for cont in cont_s:
        #     print(cont.pop().name)
        # print(GCS.graph_template is GCS_2.graph_template)

        # print(GCS.graph_attr)
        # for attr in GCS.graph_attr:
        #     print(attr)
        # attr_cs = GCS.graph_attr[0]
        # attr_cs.attr_value = 'CoordSystem_2'  # CoordSystem_2
        # attr_form_dep = GCS.graph_attr[1]
        # attr_form_dep.attr_value = 'independent'  # independent
        # attr_form_cox = GCS.graph_attr[5]
        # attr_form_cox.attr_value = 'False'  # False
        #
        # GCS.create_object()
        # print('coy = ', GCS.co_y)
        #
        # GCS.change_value(attr_cs)
        # GCS.change_value(attr_form_dep)
        # GCS.change_value(attr_form_cox)
        # print()
        # for attr in GCS.graph_attr:
        #     print(attr)
        #
        # GCS.create_object()
        # print('coy = ', GCS.co_y)

        # print(GCS.cells_route)
        # print(str(GCS))
        # print(GCS.splitter_values)

        # GNOM.register_obj_name(123, 'Cyfer')
        # GNOM.register_obj_name(1234, 'Cyfe')
        # print(GNOM.name_to_obj)
        # print(GNOM.obj_to_name)

        # print(GCS.name)
        # print(CoordinateSystem.name)
        #
        # print(ln_1.name)
        # print(ln_2.name)
        # print(ln_3.name)

        # print('eval = ', eval('nv_gdm.GNM.name_to_obj["CoordSystem_1"]'))

        # print(nv_gdm.str_to_obj('    ', 'set[Union[CoordinateSystem, Line]]'))
        # print(nv_gdm.obj_to_str(CoordinateSystem))

        # print(CoordinateSystem.mro())

        # print(CoordinateSystem.mro())
        # print(GCS.graph_template.nodes)  # .nodes

    if test == 'test_2':
        pass
        cs_1 = CoordinateSystem()
        cs_2 = CoordinateSystem()
        ln_1 = Line()
        ln_2 = Line()
        GDM.add_to_tree_graph(cs_1)
        GDM.add_to_tree_graph(cs_2)
        GDM.add_to_tree_graph(ln_1)
        GDM.add_to_tree_graph(ln_2)

        start_ni = GDM.tree_graph.inf_node_pu.ni_nd
        print(GDM.tree_graph.layered_representation(start_ni))
        print(GDM.field_graph.am.curr_context)
        print(GDM.field_graph)

        # print(GDM.tree_graph.am.curr_context)
        # print(GDM.tree_graph.am.get_single_elm_by_cell_content(PolarNode, 'CoordSystem_1'))

    if test == 'test_3':
        pass
