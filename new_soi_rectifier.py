from __future__ import annotations
from typing import Union, Iterable, Optional
from collections import OrderedDict, defaultdict
from copy import deepcopy

from cell_object import CellObject
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Link, NodeInterface
from default_ordered_dict import DefaultOrderedDict
from new_soi_objects import StationObjectImage, StationObjectDescriptor, AttribProperties, IndexManagementCommand, \
    CoordinateSystemSOI, AxisSOI, PointSOI, LineSOI, LightSOI, RailPointSOI, BorderSOI, SectionSOI
from soi_files_handler import read_station_config
from extended_itertools import flatten
from cell_access_functions import find_cell_name, element_cell_by_type

from config_names import GLOBAL_CS_NAME


class DependenciesBuildError(Exception):
    pass


class DBExistingNameError(DependenciesBuildError):
    pass


class DBCycleError(DependenciesBuildError):
    pass


class DBIsolatedNodesError(DependenciesBuildError):
    pass


class ObjNodeCell(CellObject):
    def __init__(self, cls_name: str, obj_name: str):
        self.cls_name = cls_name
        self.obj_name = obj_name


class StorageDG:
    def __init__(self):
        # gcs init
        self.gcs = CoordinateSystemSOI()
        self.gcs.name = GLOBAL_CS_NAME
        self.soi_objects: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)
        self.to_self_node_dict: defaultdict[str, dict[str, tuple[PolarNode, ObjNodeCell]]] = defaultdict(dict)
        self.to_child_attribute_dict: defaultdict[str, defaultdict[str, list[tuple]]] = \
            defaultdict(lambda: defaultdict(list))
        self.to_parent_link_dict: defaultdict[str, defaultdict[str, defaultdict[str, dict[int, Link]]]] = \
            defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self.dg = OneComponentTwoSidedPG()
        self.gcs_node = self.dg.insert_node()
        gcs_cell = ObjNodeCell("CoordinateSystemSOI", GLOBAL_CS_NAME)
        self.gcs_node.append_cell_obj(gcs_cell)

        # current object state
        self.current_object: Optional[StationObjectImage] = None
        self.current_object_is_new: bool = True

        self.bind_descriptors()
        self.reset_clean_storages()

    def bind_descriptors(self):
        for cls in StationObjectImage.__subclasses__():
            for attr_name in cls.__dict__:
                if (not attr_name.startswith("__")) and \
                        isinstance(descr := getattr(cls, attr_name), StationObjectDescriptor):
                    descr.obj_dict = self.soi_objects[descr.contains_cls_name]

    def reset_clean_storages(self):
        for cls_name in self.soi_objects:
            self.soi_objects[cls_name].clear()
        self.soi_objects["CoordinateSystemSOI"][GLOBAL_CS_NAME] = self.gcs

        self.dg = OneComponentTwoSidedPG()
        self.gcs_node = self.dg.insert_node()
        gcs_cell = ObjNodeCell("CoordinateSystemSOI", GLOBAL_CS_NAME)
        self.gcs_node.append_cell_obj(gcs_cell)

        self.to_self_node_dict.clear()
        self.to_self_node_dict["CoordinateSystemSOI"][GLOBAL_CS_NAME] = self.gcs_node, gcs_cell

        self.to_child_attribute_dict.clear()

        self.to_parent_link_dict.clear()

    # def reset_dirty_storages(self):
    #     self.dirty_soi_objects: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)
    #     self.dirty_soi_objects["CoordinateSystemSOI"][GLOBAL_CS_NAME] = self.dirty_gcs
    #     self.dirty_dg = OneComponentTwoSidedPG()
    #     self.dirty_gcs_node = self.dirty_dg.insert_node()
    #     dirty_gcs_cell = ObjNodeCell("CoordinateSystemSOI", GLOBAL_CS_NAME)
    #     self.dirty_gcs_node.append_cell_obj(dirty_gcs_cell)
    #     self.dirty_to_self_node_dict: defaultdict[str, dict[str, tuple[PolarNode, ObjNodeCell]]] = defaultdict(dict)
    #     self.dirty_to_self_node_dict["CoordinateSystemSOI"][GLOBAL_CS_NAME] = self.dirty_gcs_node, dirty_gcs_cell
    #     self.dirty_to_child_attribute_dict: defaultdict[str, defaultdict[str, list[tuple]]] = \
    #         defaultdict(lambda: defaultdict(list))
    #     self.dirty_to_parent_link_dict: defaultdict[str, defaultdict[str, defaultdict[str, dict[int, Link]]]] = \
    #         defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    def reload_from_dict(self, od: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]]):
        self.reset_clean_storages()

        # Stage 1 - names, nodes and their cells initialization
        for cls_name in od:
            for obj_name, obj in od[cls_name].items():
                if obj_name == GLOBAL_CS_NAME:
                    continue
                self.init_obj_node_dg(obj)
        # print("soi", self.soi_objects)

        # Stage 3 - nodes connections relied on formal requirements to attributes
        for cls_name in od:
            for obj_name, obj in od[cls_name].items():
                if obj_name == GLOBAL_CS_NAME:
                    continue
                self.insert_obj_to_dg(obj)
                self.obj_attrib_evaluation(obj)

        # Stage 5 - check cycles
        self.full_check_cycle_dg()

    def obj_attrib_evaluation(self, obj: StationObjectImage):
        obj_name = obj.name
        if obj_name != GLOBAL_CS_NAME:
            for attr_name in obj.active_attrs:
                descr = getattr(obj.__class__, attr_name)
                if isinstance(descr, StationObjectDescriptor):
                    obj.reload_attr_value(attr_name)

    def init_obj_node_dg(self, obj: StationObjectImage):
        # print("obj", obj)
        cls_name = obj.__class__.__name__
        obj_name = obj.name
        self.soi_objects[cls_name][obj_name] = obj
        obj: StationObjectImage
        node = self.dg.insert_node()
        cell = ObjNodeCell(cls_name, obj_name)
        node.append_cell_obj(cell)
        self.to_self_node_dict[cls_name][obj_name] = node, cell

    def insert_obj_to_dg(self, obj: StationObjectImage):
        cls_name = obj.__class__.__name__
        obj_name = obj.name
        for attr_name in obj.active_attrs:
            # print("active_attrs", attr_name)
            if (not attr_name.startswith("__")) and \
                    isinstance(descr := getattr(obj.__class__, attr_name), StationObjectDescriptor):
                contains_cls_name = descr.contains_cls_name
                obj_names_dict = self.soi_objects[contains_cls_name]
                attr_prop_str_values = obj.list_attr_input_value(attr_name)
                for index, parent_name in enumerate(attr_prop_str_values):
                    if len(attr_prop_str_values) == 1:
                        index = -1
                    if parent_name in obj_names_dict:
                        self_node = self.to_self_node_dict[cls_name][obj_name][0]
                        parent_node = self.to_self_node_dict[contains_cls_name][parent_name][0]
                        self.to_child_attribute_dict[contains_cls_name][parent_name].append(
                            (obj, attr_name, index))
                        link = self.dg.connect_inf_handling(self_node.ni_pu, parent_node.ni_nd)
                        self.to_parent_link_dict[cls_name][obj_name][attr_name][index] = link

    def full_check_cycle_dg(self):
        routes = self.dg.walk(self.dg.inf_pu.ni_nd)
        route_nodes = set()
        for route in routes:
            route_nodes |= set(route.nodes)
        if len(route_nodes) < len(self.dg.nodes):
            nodes = self.dg.nodes - route_nodes
            obj_names: list[str] = [element_cell_by_type(node, ObjNodeCell).obj_name for node in nodes]
            raise DBIsolatedNodesError("", ", ".join(obj_names), "", "Isolated nodes was found")
        for route_ in routes:
            if route_.is_cycle:
                end_node = route_.nodes[-1]
                obj_name = element_cell_by_type(end_node, ObjNodeCell).obj_name
                raise DBCycleError("", obj_name, "", "Cycle in dependencies was found")

    def rectify_dg(self) -> list[StationObjectImage]:
        nodes: list[PolarNode] = list(flatten(self.dg.longest_coverage()))[1:]  # without Global CS
        result = []
        for node in nodes:
            cell = element_cell_by_type(node, ObjNodeCell)
            result.append(self.soi_objects[cell.cls_name][cell.obj_name])
        return result

    def dependent_objects_names(self, cls_name: str, obj_name: str) -> list[tuple[str, str]]:
        self_node = self.to_self_node_dict[cls_name][obj_name][0]
        dependent_nodes = list(flatten(self.dg.shortest_coverage(self_node.ni_nd)))
        result = []
        for node in dependent_nodes:
            cell: ObjNodeCell = element_cell_by_type(node, ObjNodeCell)
            result.append((cell.cls_name, cell.obj_name))
        return result

    def delete_object(self, cls_name: str, obj_name: str) -> list[tuple[str, str]]:
        """ clean operation - to main dg immediately """
        dependent_objects_names = self.dependent_objects_names(cls_name, obj_name)
        new_soi_objects: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)
        for cls_name in self.soi_objects:
            for obj_name in self.soi_objects[cls_name]:
                if (cls_name, obj_name) not in dependent_objects_names:
                    new_soi_objects[cls_name][obj_name] = self.soi_objects[cls_name][obj_name]
        self.reload_from_dict(new_soi_objects)
        return dependent_objects_names

    def rename_object(self, cls_name: str, old_obj_name: str, new_obj_name: str):
        """ clean operation - to main dg immediately """

        # 2. rename obj in dicts and in cell
        obj_dict = self.soi_objects[cls_name]
        obj = obj_dict[old_obj_name]
        obj_dict[new_obj_name] = obj
        obj_dict.pop(old_obj_name)

        cell = self.to_self_node_dict[cls_name][old_obj_name][1]
        cell.obj_name = new_obj_name

        self.to_self_node_dict[cls_name][new_obj_name] = self.to_self_node_dict[cls_name][old_obj_name]
        self.to_self_node_dict[cls_name].pop(old_obj_name)

        self.to_child_attribute_dict[cls_name][new_obj_name] = self.to_child_attribute_dict[cls_name][old_obj_name]
        self.to_child_attribute_dict[cls_name].pop(old_obj_name)

        # 3. rename obj
        obj.change_attrib_value("name", new_obj_name)

        # 4. rename obj in dependent attributes
        for dependent_obj_tuple in self.to_child_attribute_dict[cls_name][new_obj_name]:
            dependent_obj, attr_name, index = dependent_obj_tuple
            dependent_obj.change_attrib_value(attr_name, new_obj_name, index)

    def select_current_object(self, cls_name: str, obj_name: str):
        """ clean operation """
        self.current_object = self.soi_objects[cls_name][obj_name]
        self.current_object_is_new = False

    def create_empty_new_object(self, cls_name: str):
        """ clean operation """
        self.current_object: StationObjectImage = eval(cls_name)()
        self.current_object_is_new = True

    def apply_creation_current_object(self):
        """ clean operation """
        self.init_obj_node_dg(self.current_object)
        self.insert_obj_to_dg(self.current_object)

    # def clean_to_dirty(self):
    #     self.dirty_dg = self.dg.copy_part()
    #
    #     self.dirty_soi_objects = deepcopy(self.soi_objects)
    #     self.dirty_to_self_node_dict = deepcopy(self.to_self_node_dict)
    #     self.dirty_to_child_attribute_dict = deepcopy(self.to_child_attribute_dict)
    #     self.dirty_to_parent_link_dict = deepcopy(self.to_parent_link_dict)
    #
    # def dirty_to_clean(self):
    #     self.dg = self.dirty_dg

    def change_attrib_value_main(self, attr_name: str, new_value: str, index: int = -1):
        """ main change attrib value function """
        new_value = new_value.strip()
        cls_name = self.current_object.__class__.__name__
        obj_name = self.current_object.name
        obj = self.current_object
        obj_dict = self.soi_objects[cls_name]

        old_value = obj.single_attr_input_value(attr_name, index)
        if new_value == old_value:
            print("value not changed")
            return

        if attr_name == "name":
            if new_value in obj_dict:
                raise DBExistingNameError(cls_name, obj_name, "name", "Name {} already exists".format(new_value))
            if self.current_object_is_new:
                self.current_object.change_attrib_value("name", new_value)
            else:
                self.rename_object(cls_name, obj_name, new_value)
        else:
            if self.current_object_is_new:
                self.current_object.change_attrib_value(attr_name, new_value, index)
            else:
                self.change_attrib_value_existing(attr_name, new_value, index)

    def try_change_attr_value(self, cls_name: str, obj_name: str, attr_name: str, new_value: str, index: int,
                              contains_cls_name: str) -> Optional[tuple[Link, tuple[NodeInterface, NodeInterface]]]:
        contain_dict = self.soi_objects[contains_cls_name]
        if new_value not in contain_dict:
            return
        else:
            dirty_dg = self.dg.copy_part()

            # old value disconnection
            link_dg = self.to_parent_link_dict[cls_name][obj_name][attr_name][index]
            link_dirty_dg = dirty_dg.link_copy_mapping[link_dg]
            dirty_dg.disconnect_inf_handling(*link_dirty_dg.ni_s)

            # new value connection
            self_node = self.to_self_node_dict[cls_name][obj_name][0]
            parent_node = self.to_self_node_dict[contains_cls_name][new_value][0]
            dirty_self_node = dirty_dg.node_copy_mapping[self_node]
            dirty_parent_node = dirty_dg.node_copy_mapping[parent_node]
            new_link = dirty_dg.connect_inf_handling(dirty_self_node.ni_pu, dirty_parent_node.ni_nd)

            # check cycles
            for ni in new_link.ni_s:
                routes = dirty_dg.walk(ni)
                for route_ in routes:
                    if route_.is_cycle:
                        end_node = route_.nodes[-1]
                        obj_name = element_cell_by_type(end_node, ObjNodeCell).obj_name
                        raise DBCycleError(cls_name, obj_name, attr_name, "Cycle in dependencies was found")
            return link_dg, (self_node.ni_pu, parent_node.ni_nd)

    def change_attrib_value_existing(self, attr_name: str, new_value: str, index: int):
        """ dirty operation """
        cls_name = self.current_object.__class__.__name__
        obj_name = self.current_object.name
        obj = self.current_object
        descr = getattr(obj.__class__, attr_name)
        if isinstance(descr, StationObjectDescriptor):
            contains_cls_name = descr.contains_cls_name
            try_result = self.try_change_attr_value(cls_name, obj_name, attr_name, new_value, index, contains_cls_name)
            if not (try_result is None):
                old_link, new_ni_tuple = try_result
                self.dg.disconnect_inf_handling(*old_link.ni_s)
                new_link = self.dg.connect_inf_handling(*new_ni_tuple)
                self.to_parent_link_dict[cls_name][obj_name][attr_name][index] = new_link
        obj.change_attrib_value(attr_name, new_value, index)


if __name__ == "__main__":
    test_1 = True
    if test_1:
        # print("r")
        r = StorageDG()
        config_objs = read_station_config("station_in_config")
        # print("read_station_config")
        r.reload_from_dict(config_objs)
        # print(len(r.dg.links))
        # print("delete : ", r.delete_object("AxisSOI", "Axis_2"))
        # print(len(r.dg.links))
        # print(r.dg.links)
        # print(r.dg.nodes)

        # r.change_attrib_value("Point_15", "LineSOI", "Line_7", "points", 0)

        # sec_dg = r.dg.copy_part()
        # print(len(sec_dg.links))
        print(r.soi_objects["PointSOI"]["Point_10"])
        print([obj.name for obj in r.rectify_dg()])
        r.select_current_object("LineSOI", "Line_7")
        r.change_attrib_value_main("points", "Point_10", 1)
        # print(r.dependent_objects_names("PointSOI", "Point_18"))
        # r.select_current_object("PointSOI", "Point_18")
        # r.change_attrib_value_main("name", "Point_180")
        # print([obj.name for obj in r.rectify_dg()])
        # print(r.dependent_objects_names("PointSOI", "Point_180"))
        print(r.soi_objects["LineSOI"]["Line_7"].points)
