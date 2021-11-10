from __future__ import annotations
import re
from copy import copy
# import time

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
from nv_cell import Cell, BSSCellType
#  , DefaultCellChecker, NameCellChecker, SplitterCellChecker, BoolCellChecker, NameAutoSetter, GNM
from nv_config import CLASSES_SEQUENCE, GROUND_CS_NAME, NEW_OBJECT_NAME
from nv_errors import CycleError, CycleCellError

BSSDependency = bounded_string_set('BSSDependency', [['dependent'], ['independent']])
BSSBool = bounded_string_set('BSSBool', [['True'], ['False']])


class GlobalNamesManager:
    def __init__(self):
        self._name_to_obj: dict[str, Any] = {}
        self._obj_to_name: dict[Any, str] = {}  # for check obj repeating

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


# def auto_name(cell: Cell):
#     return
#
#
# def check_syntax_name(cell: Cell):
#     return
#
#
# def check_syntax_default(cell: Cell):
#     return
#
#
# def check_syntax_common_splitter(cell: Cell):
#     return
#
#
# def check_syntax_bool_splitter(cell: Cell):
#     return
#
#
# def check_type(cell: Cell):
#     return
#
#
# def check_dependence_loop(cell: Cell):
#     return
#
#
# default_pipeline = [check_syntax_default, check_type, check_dependence_loop]
# name_standard_pipeline = [auto_name, check_syntax_name]
# common_splitter_pipeline = [check_syntax_common_splitter]
# bool_splitter_pipeline = [check_syntax_bool_splitter]


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
            graph_template_.am.bind_cell(move_, unique_value)


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

            a_m.bind_cell(node_rel_cs, Cell('cs_relative_to', 'CoordinateSystem'))
            a_m.bind_cell(node_check_dependence,
                          Cell('dependence', 'BSSDependency', 'independent', BSSCellType('common_splitter')))
            a_m.bind_cell(node_x, Cell('x', 'int'))
            a_m.bind_cell(move_to_x, Cell('dependent'))
            a_m.bind_cell(node_y, Cell('y', 'int'))
            a_m.bind_cell(node_alpha, Cell('alpha', 'int'))
            a_m.bind_cell(move_to_alpha, Cell('independent'))
            a_m.bind_cell(node_connect_polarity,
                          Cell('connection_polarity', 'End', 'negative_down', BSSCellType('common_splitter')))
            a_m.bind_cell(node_co_x, Cell('co_x', 'BSSBool', 'True', BSSCellType('bool_splitter')))
            a_m.bind_cell(node_co_y, Cell('co_y', 'BSSBool', 'True', BSSCellType('bool_splitter')))

        if owner == Point:
            node_rel_cs, _, _ = g_b_t.insert_node_single_link()

            a_m.bind_cell(node_rel_cs, Cell('cs_relative_to', 'CoordinateSystem'))

        if owner == Line:
            node_rel_cs, _, _ = g_b_t.insert_node_single_link()

            a_m.bind_cell(node_rel_cs, Cell('cs_relative_to', 'CoordinateSystem'))

        if owner == GroundLine:
            node_rel_cs, _, _ = g_b_t.insert_node_single_link()

            a_m.bind_cell(node_rel_cs, Cell('cs_relative_to', 'CoordinateSystem'))

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

        a_m.bind_cell(node_name_title, Cell('Name options'))
        a_m.bind_cell(node_name, Cell('name', owner.__name__, cell_type=BSSCellType('name')))
        a_m.bind_cell(node_build_title, Cell('Build options'))
        a_m.bind_cell(node_evaluate_title, Cell('Evaluation options'))
        a_m.bind_cell(node_view_title, Cell('View options'))

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
    send_single_value = pyqtSignal(AttributeFormat)
    send_class_str = pyqtSignal(str)
    create_readiness = pyqtSignal(bool)
    default_attrib_list = [AttributeFormat(BSSAttributeType('title'), '<pick object>')]
    new_str_tree = pyqtSignal(dict)

    send_info_object = pyqtSignal(list)

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

    def form_attrib_list(self, obj, need_to_check=True):
        if obj is None:
            return self.default_attrib_list
        af_list: list[AttributeFormat] = []
        g = obj.graph_template
        am = g.am
        for node in g.not_inf_nodes:
            cells = am.cell_dicts[node].values()
            for cell in cells:
                cell.deactivate()
        fr = g.free_roll()
        cells_set_list = am.extract_route_content(fr)
        splitter_cells_set = [i[1] for i in get_splitter_nodes_cells(g)]
        for i, set_cells in enumerate(cells_set_list):
            if not set_cells:
                continue
            cell = set_cells.pop()
            out_name = name_translator_storage_to_interface(cell.name)
            if cell in splitter_cells_set:
                str_value = cells_set_list[i + 1].pop().name
                cls = get_class_by_str(cell.checker.req_class_str)
                cell.str_value = str_value
                af = AttributeFormat(BSSAttributeType('splitter'), out_name, cell.str_value, cls.unique_values)
                cell.activate()
            elif cell.checker is None:
                af = AttributeFormat(BSSAttributeType('title'), out_name)
            else:
                cell.activate()
                af = AttributeFormat(BSSAttributeType('str_value'), out_name, cell.str_value)
                af.is_suggested = cell.is_suggested_value

            if need_to_check:
                cell.check_value()
            af.status_check = cell.status_check
            if cell.checker and hasattr(cell.checker, 'req_class_str'):
                af.req_type_str = 'Required type: {}'.format(cell.checker.req_class_str)
            af_list.append(af)

        return af_list

    @pyqtSlot(str)
    def change_current_object(self, obj_name: str):
        GDM.delete_temporary_dependence()
        self.current_object = GNM.name_to_obj[obj_name]
        self._is_new_object = False
        self.send_current_obj_attribs()

    @pyqtSlot(str)
    def create_new_object(self, obj_type: str):
        GDM.delete_temporary_dependence()
        new_object = eval(obj_type)()
        self.current_object = new_object
        self._is_new_object = True
        self.send_current_obj_attribs()

    def send_current_obj_attribs(self):
        self.send_class_str.emit(self.current_object.__class__.__name__)
        af_list = self.form_attrib_list(self.current_object)
        self.send_attrib_list.emit(af_list)
        self.check_all_values_defined()

    @pyqtSlot(str, str)
    def slot_change_value(self, name_interface: str, new_value: str):
        name = name_translator_interface_to_storage(name_interface)
        curr_obj = self.current_object
        g = curr_obj.graph_template
        node: PolarNode = g.am.get_single_elm_by_cell_content(PolarNode, name)
        assert node, 'Node not found'
        node_cell: Cell = g.am.get_elm_cell_by_context(node)
        assert node_cell, 'Node cell not found'
        node_cell.str_value = new_value
        # if GDM.loop_dependence_checker in node_cell.checker.f_check_semantic_list:  # GDM.loop_dependence_checker
        GDM.current_object = curr_obj
        #     GDM.current_cell = node_cell
        if node in [i[0] for i in get_splitter_nodes_cells(g)]:
            move = g.am.get_single_elm_by_cell_content(PGMove, new_value, node.ni_nd.moves)
            assert move, 'Move not found'
            node.ni_nd.choice_move_activate(move)
        af_list = self.form_attrib_list(self.current_object)
        if isinstance(node_cell.checker, DefaultCellChecker) and node_cell.checker.req_class_str in CLASSES_SEQUENCE:
            GDM.check_dependence_loop(curr_obj, node_cell)
        self.send_attrib_list.emit(af_list)
        self.check_all_values_defined()

    def get_active_cells(self) -> set[Cell]:
        curr_obj = self.current_object
        g = curr_obj.graph_template
        return {g.am.get_elm_cell_by_context(node) for node in g.am.get_filter_all_cells(PolarNode)}

    def check_all_values_defined(self) -> bool:
        self._create_readiness = all(not(active_cell.value is None) for active_cell in self.get_active_cells())
        self.create_readiness.emit(self._create_readiness)
        return self._create_readiness

    def create_obj_attributes(self):
        curr_obj = self.current_object
        for active_cell in self.get_active_cells():
            assert re.fullmatch(r'\w+', active_cell.name), 'Name {} for attr is not possible'.format(active_cell.name)
            setattr(curr_obj, active_cell.name, active_cell.value)

    @pyqtSlot()
    def apply_changes(self):
        co = self.current_object
        if self.check_all_values_defined():
            self.create_obj_attributes()
            if co in GNM.obj_to_name:
                old_name = GNM.obj_to_name[co]
                GNM.rename_obj(co, co.name)
                GDM.rename_cell_in_tree(old_name, co.name)  # co,
                print('rename for existing')
                GDM.rename_cells_in_dependence_graph(old_name, co.name)
            else:
                GDM.add_new_class_instance(co)
                GDM.add_to_tree_graph(co)
                GNM.register_obj_name(co, co.name)
                print('rename for new')
                GDM.rename_cells_in_dependence_graph(NEW_OBJECT_NAME, co.name)
        self.create_new_object(co.__class__.__name__)
        self.new_str_tree.emit(GDM.tree_graph_dict_string_repr)

    @pyqtSlot()
    def get_tree_graph(self):
        self.new_str_tree.emit(GDM.tree_graph_dict_string_repr)

    @pyqtSlot(str)
    def hover_handling(self, obj_name):
        if obj_name != GDM.gcs.name:
            af_list = self.form_attrib_list(GNM.name_to_obj[obj_name], False)
            self.send_info_object.emit(af_list)


CAI = CommonAttributeInterface()


class GlobalDataManager:

    def __init__(self):
        self._tree_graph = BasePolarGraph()
        self._dependence_graph = BasePolarGraph()
        self._field_graph = BasePolarGraph()

        self._class_instances: dict[str, list[AttrControlObject]] = {}

        self.init_tree_graph()
        self.init_dependence_graph()

        self._gcs = None
        self.init_field_graph()
        self.init_global_coordinate_system()

        # self.current_cell = None
        # self.current_object = None

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
        for cls_name in CLASSES_SEQUENCE:
            node_class, _, _ = self.tree_graph.insert_node_single_link()
            a_m.bind_cell(node_class, cls_name)

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
        self._gcs.name = GROUND_CS_NAME
        GNM.register_obj_name(self._gcs, GROUND_CS_NAME)
        self.add_new_class_instance(self._gcs)
        self.add_to_tree_graph(self._gcs)

        dg = self.dependence_graph
        a_m = dg.am
        gcs_node, _, _ = dg.insert_node_single_link()
        a_m.bind_cell(gcs_node, GROUND_CS_NAME)

    @property
    def gcs(self) -> CoordinateSystem:
        return self._gcs

    def add_new_class_instance(self, obj: AttrControlObject):
        cls_name = obj.__class__.__name__
        if cls_name not in self._class_instances:
            self._class_instances[cls_name] = list()
        self._class_instances[cls_name].append(obj)

    def add_to_tree_graph(self, obj: AttrControlObject):
        tg = self.tree_graph
        a_m = tg.am
        node_class = a_m.get_single_elm_by_cell_content(PolarNode, obj.__class__.__name__)
        assert node_class, 'Node class not found'
        node_obj, _, _ = tg.insert_node_single_link(node_class.ni_nd)
        a_m.bind_cell(node_obj, obj.name)

    def auto_set_name(self, cell: Cell, obj: AttrControlObject = None):
        if cell.cell_type == 'name':
            prefix = obj.__class__.__name__ + '_'
            i = 1
            while True:
                auto_name = '{}{}'.format(prefix, i)
                if GNM.check_new_name(auto_name):
                    break
                else:
                    i += 1
            cell.str_value = auto_name

    def syntax_check(self, cell: Cell, obj: AttrControlObject = None):
        if cell.str_value == '':
            return
        if cell.str_req == '':
            return

        if cell.cell_type == 'common_splitter' or cell.cell_type == 'bool_splitter':
            cls = eval(cell.str_req)
            if cell.str_value not in cls.possible_strings:
                cell.status_check = 'Value of splitter not in possible values'
                return
            else:
                if cell.cell_type == 'common_splitter':
                    cell.value = cell.str_value
                    return
                if cell.cell_type == 'bool_splitter':
                    cell.value = eval(cell.str_value)
                    return

        if cell.cell_type == 'name':
            if (cell.str_value in GNM.name_to_obj) and (cell.value == GNM.name_to_obj[cell.str_value]):
                return
            prefix = cell.str_req + '_'
            if not re.fullmatch(r'\w+', cell.str_value):
                cell.status_check = 'Name have to consists of alphas, nums and _'
            if not cell.str_value.startswith(prefix):
                cell.status_check = 'Name have to begin from ClassName_'
            if cell.str_value == prefix:
                cell.status_check = 'Name cannot be == prefix; add specification to end'
            if not GNM.check_new_name(cell.str_value):
                cell.status_check = 'Name {} already exists'.format(cell.str_value)
            cell.value = obj
            return

        if cell.cell_type == 'default':
            str_value_copy = cell.str_value
            found_identifier_candidates = re.findall(r'\w+', str_value_copy)
            for fic in found_identifier_candidates:
                if fic in GNM.name_to_obj:
                    str_value_copy = str_value_copy.replace(fic, 'GNM.name_to_obj["{}"]'.format(fic))
            try:
                eval_result = eval(str_value_copy)
            except SyntaxError:
                cell.status_check = 'Syntax error when parsing ' + cell.str_value
            except NameError:
                cell.status_check = 'Name error when parsing ' + cell.str_value
            else:
                cell.eval_buffer = eval_result

    def check_dependence_loop(self, curr_obj, node_cell):
        print('CHECK LOOP')
        cell_str_value = node_cell.str_value
        dg = self.dependence_graph
        a_m = dg.am
        print('before - len of not inf nodes', len(dg.not_inf_nodes))
        print('before - len of links', len(dg.links))

        obj_name = NEW_OBJECT_NAME
        if hasattr(curr_obj, 'name'):
            obj_name = curr_obj.name
        obj_node = a_m.get_single_elm_by_cell_content(PolarNode, obj_name)
        if obj_node is None:
            print('obj node not found!')
            obj_node, _, _ = dg.insert_node_single_link()
            a_m.bind_cell(obj_node, obj_name)

        attr_name = node_cell.name
        attr_full_name = '{}.{}'.format(obj_name, attr_name)
        attr_node = a_m.get_single_elm_by_cell_content(PolarNode, attr_full_name)
        if attr_node:
            print('attr node found!')
            for link in attr_node.ni_pu.links:
                dg.disconnect_nodes_auto_inf_handling(*link.ni_s)
        # print('attr_full_name', attr_full_name)

        found_identifier_candidates = re.findall(r'\w+', cell_str_value)
        for fic in found_identifier_candidates:
            if fic in GNM.name_to_obj:
                parent_obj_node = a_m.get_single_elm_by_cell_content(PolarNode, fic)
                print('fic', fic)
                assert parent_obj_node, 'Parent_obj_node not found'
                if attr_node is None:
                    attr_node, _, _ = dg.insert_node_single_link(parent_obj_node.ni_nd, obj_node.ni_pu)
                    a_m.bind_cell(attr_node, attr_full_name)
                else:
                    dg.connect_nodes_auto_inf_handling(parent_obj_node.ni_nd, attr_node.ni_pu)

        if (len(attr_node.ni_pu.links) == 1) and (attr_node.ni_pu.links.pop().opposite_ni is dg.inf_node_pu.ni_nd):
            dg.remove_nodes([attr_node])

        print('after - len of not inf nodes', len(dg.not_inf_nodes))
        print('after - len of links', len(dg.links))
        for i, link in enumerate(dg.links):
            print('link #{}'.format(i+1), 'between', [(a_m.get_elm_cell_by_context(ni.pn).name, ni.end)
                                                      for ni in link.ni_s if ni.pn not in dg.inf_nodes])
            # print('between', [(a_m.get_elm_cell_by_context(ni.pn).name, ni.end) for ni in link.ni_s
            #                       if ni.pn not in dg.inf_nodes])

    # def loop_dependence_checker(self, cell_str_value, cell_value):
    #     self.refresh_dependence_graph(cell_str_value)
    #     dg = self.dependence_graph
        if not dg.check_loops():
            raise CycleCellError('Dependence cycle was found')

    def delete_temporary_dependence(self):
        print('delete temporary dependence')
        dg = self.dependence_graph
        a_m = dg.am
        a_m.filter_function = lambda x: NEW_OBJECT_NAME in x.name
        nodes_found = a_m.get_filter_all_cells(PolarNode)
        dg.remove_nodes(nodes_found)

    def add_cell_to_dependence_graph(self, cell: Cell, obj: AttrControlObject):
        dg = self.dependence_graph
        am_dg = dg.am

    @property
    def tree_graph_dict_string_repr(self) -> dict[str, list[str]]:
        tg = self.tree_graph
        a_m = tg.am
        result = {}
        first_ni = tg.inf_node_pu.ni_nd
        for move in first_ni.ordered_moves:
            node_of_class = move.link.opposite_ni(first_ni).pn
            cell_class = a_m.get_elm_cell_by_context(node_of_class)
            obj_moves = node_of_class.ni_nd.ordered_moves
            child_pns = list(move.link.opposite_ni(node_of_class.ni_nd).pn
                             for move in obj_moves)
            if tg.inf_node_nd in child_pns:
                result[cell_class.name] = []
                continue
            child_names = list(a_m.get_elm_cell_by_context(child_pn).name for child_pn in child_pns)
            result[cell_class.name] = child_names
        return result

    def rename_cells_in_dependence_graph(self, old_name: str, new_name: str):
        print('rename from {} to {}'.format(old_name, new_name))
        dg = self.dependence_graph
        a_m = dg.am
        a_m.filter_function = lambda x: old_name in x.name
        nodes_found = a_m.get_filter_all_cells(PolarNode)
        for node in nodes_found:
            cell = a_m.get_elm_cell_by_context(node)
            cell.name = cell.name.replace(old_name, new_name)

    def rename_cell_in_tree(self, old_name: str, new_name: str):  # , obj: AttrControlObject
        tg = self.tree_graph
        a_m = tg.am
        found = False
        for grph_elem_cls in a_m.curr_context:
            elm = a_m.get_single_elm_by_cell_content(grph_elem_cls, old_name)
            if elm is None:
                continue
            found = True
            cell = a_m.get_elm_cell_by_context(elm)
            cell.name = new_name
        assert found, 'Not found'

    def get_obj_by_cell(self, cell: Cell):
        pass


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
