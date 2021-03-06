from __future__ import annotations
from typing import Union, Iterable, Optional
from collections import OrderedDict, defaultdict
from copy import deepcopy, copy

from cell_object import CellObject
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Link, NodeInterface
from default_ordered_dict import DefaultOrderedDict
from soi_objects import StationObjectImage, StationObjectDescriptor, AttribValues, IndexManagementCommand, \
    CoordinateSystemSOI, AxisSOI, PointSOI, LineSOI, LightSOI, RailPointSOI, BorderSOI, SectionSOI, \
    AttributeEvaluateError, NameDescriptor
from soi_files_handler import read_station_config
from extended_itertools import flatten
from cell_access_functions import find_cell_name, element_cell_by_type
from attribute_object_key import AttributeKey

from config_names import GLOBAL_CS_NAME


class DependenciesBuildError(Exception):
    pass


class DBExistingNameError(DependenciesBuildError):
    pass


class DBCycleError(DependenciesBuildError):
    pass


class DBIsolatedNodesError(DependenciesBuildError):
    pass


class DBAttributeError(DependenciesBuildError):
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
        self.link_to_attribute_dict: dict[Link, AttributeKey] = {}
        self.to_parent_link_dict: defaultdict[str, defaultdict[str, defaultdict[str, dict[int, Link]]]] = \
            defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self.dg = OneComponentTwoSidedPG()
        self.gcs_node = self.dg.insert_node()
        gcs_cell = ObjNodeCell("CoordinateSystemSOI", GLOBAL_CS_NAME)
        self.gcs_node.append_cell_obj(gcs_cell)

        # current object state
        self.current_object: Optional[StationObjectImage] = None
        self.current_object_is_new: bool = True
        self.backup_soi = DefaultOrderedDict(OrderedDict)

        self.init_soi_classes()
        self.bind_descriptors()
        self.reset_clean_storages()

    def init_soi_classes(self):
        for cls in StationObjectImage.__subclasses__():
            self.soi_objects[cls.__name__]

    def bind_descriptors(self):
        for cls in StationObjectImage.__subclasses__():
            for attr_name in cls.__dict__:
                if not attr_name.startswith("__"):
                    if isinstance(descr := getattr(cls, attr_name), StationObjectDescriptor):
                        descr.obj_dict = self.soi_objects[descr.contains_cls_name]
                    if isinstance(descr := getattr(cls, attr_name), NameDescriptor):
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
        self.link_to_attribute_dict.clear()

        self.to_parent_link_dict.clear()
        # print("soi_objects", self.soi_objects)

    def save_state(self):
        self.backup_soi = DefaultOrderedDict(OrderedDict)
        for cls_name in self.soi_objects:
            for obj_name, obj in self.soi_objects[cls_name].items():
                self.backup_soi[cls_name][obj_name] = obj

    def reload_from_dict(self, od: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]]) -> \
            None:
        self.save_state()
        self.reset_clean_storages()

        # Stage 1 - add names, nodes and their cells initialization
        for cls_name in od:
            for obj_name, obj in od[cls_name].items():
                if obj_name == GLOBAL_CS_NAME:
                    continue
                self.add_obj_to_soi(obj)
                self.init_obj_node_dg(obj)

        # Stage 2 - nodes connections and attributes reload
        for cls_name in od:
            for obj_name, obj in od[cls_name].items():
                if obj_name == GLOBAL_CS_NAME:
                    continue
                self.obj_attrib_evaluation(obj)
                self.make_obj_conections(obj)

        # Stage 3 - check cycles
        self.full_check_cycle_dg()

    def obj_attrib_evaluation(self, obj: StationObjectImage):
        cls_name = obj.__class__.__name__
        obj_name = obj.name
        if obj_name != GLOBAL_CS_NAME:
            for attr_name in obj.active_attrs:
                descr = getattr(obj.__class__, attr_name)
                if isinstance(descr, StationObjectDescriptor):
                    try:
                        obj.reload_attr_value(attr_name)
                    except AttributeEvaluateError as e:
                        raise DBAttributeError(e.args[0], e.args[1])

    def add_obj_to_soi(self, obj: StationObjectImage):
        cls_name = obj.__class__.__name__
        obj_name = obj.name
        self.soi_objects[cls_name][obj_name] = obj

    def init_obj_node_dg(self, obj: StationObjectImage):
        cls_name = obj.__class__.__name__
        obj_name = obj.name
        node = self.dg.insert_node()
        cell = ObjNodeCell(cls_name, obj_name)
        node.append_cell_obj(cell)
        self.to_self_node_dict[cls_name][obj_name] = node, cell

    def make_obj_conections(self, obj: StationObjectImage):
        cls_name = obj.__class__.__name__
        obj_name = obj.name
        for attr_name in obj.active_attrs:
            if (not attr_name.startswith("__")) and \
                    isinstance(descr := getattr(obj.__class__, attr_name), StationObjectDescriptor):
                contains_cls_name = descr.contains_cls_name
                obj_names_dict = self.soi_objects[contains_cls_name]
                attr_prop_str_values = obj.list_attr_str_confirmed_value(attr_name)
                for index, parent_name in enumerate(attr_prop_str_values):
                    if len(attr_prop_str_values) == 1:
                        index = -1
                    if parent_name in obj_names_dict:
                        self_node = self.to_self_node_dict[cls_name][obj_name][0]
                        parent_node = self.to_self_node_dict[contains_cls_name][parent_name][0]
                        self.to_child_attribute_dict[contains_cls_name][parent_name].append((obj, attr_name, index))
                        link = self.dg.connect_inf_handling(self_node.ni_pu, parent_node.ni_nd)
                        self.to_parent_link_dict[cls_name][obj_name][attr_name][index] = link
                        self.link_to_attribute_dict[link] = AttributeKey(cls_name, obj_name, attr_name, index)

    def full_check_cycle_dg(self):
        routes = self.dg.walk(self.dg.inf_pu.ni_nd)
        route_links = set()
        for route in routes:
            route_links |= set(route.links)
        if len(route_links) < len(self.dg.links):
            links = self.dg.links - route_links
            raise DBIsolatedNodesError("Isolated cycles in dependencies was found",
                                       [self.link_to_attribute_dict[link] for link in links])
        for route_ in routes:
            if route_.is_cycle:
                links = route_.cycle_links
                raise DBCycleError("Cycle in dependencies was found",
                                   [self.link_to_attribute_dict[link] for link in links])

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

    def delete_object(self, cls_name: str, obj_name: str) -> \
            DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]]:  #
        """ clean operation - to main dg immediately """
        dependent_objects_names = self.dependent_objects_names(cls_name, obj_name)
        new_soi_objects: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)
        deleted_soi_objects: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = \
            DefaultOrderedDict(OrderedDict)
        for cls_name in self.soi_objects:
            for obj_name in self.soi_objects[cls_name]:
                if (cls_name, obj_name) not in dependent_objects_names:
                    new_soi_objects[cls_name][obj_name] = self.soi_objects[cls_name][obj_name]
                else:
                    deleted_soi_objects[cls_name][obj_name] = self.soi_objects[cls_name][obj_name]
        """ reload - not effective """
        self.reload_from_dict(new_soi_objects)
        return deleted_soi_objects

    def recover_objects(self, rec_obj: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]]):
        new_soi_objects = DefaultOrderedDict(OrderedDict)
        for cls_name in self.soi_objects:
            for obj_name, obj in self.soi_objects[cls_name].items():
                new_soi_objects[cls_name][obj_name] = obj
        for cls_name in rec_obj:
            for obj_name, obj in rec_obj[cls_name].items():
                new_soi_objects[cls_name][obj_name] = obj
        """ reload - not effective """
        self.reload_from_dict(new_soi_objects)

    def select_current_object(self, cls_name: str, obj_name: str) -> tuple[str, str]:
        """ clean operation """
        backup = self.current_object
        if cls_name == "reset":
            self.current_object = None
            self.current_object_is_new = True
        else:
            self.current_object = self.soi_objects[cls_name][obj_name]
            self.current_object_is_new = False
        if backup:
            return backup.__class__.__name__, backup.name
        else:
            return "reset", ""

    def create_empty_new_object(self, cls_name: str) -> tuple[str, str]:
        """ clean operation """
        backup = self.current_object
        self.current_object: StationObjectImage = eval(cls_name)()
        self.current_object_is_new = True
        if backup:
            return backup.__class__.__name__, backup.name
        else:
            return "reset", ""

    def apply_creation_current_object(self) -> tuple[str, str]:
        """ clean operation """
        # print("apply_creation")
        self.add_obj_to_soi(self.current_object)
        self.init_obj_node_dg(self.current_object)
        self.make_obj_conections(self.current_object)
        return self.current_object.__class__.__name__, self.current_object.name

    def change_attrib_value_main(self, attr_name: str, new_value: str, index: int = -1) -> str:
        """ main change attrib value function """
        new_value = new_value.strip()
        cls_name = self.current_object.__class__.__name__
        obj_name = self.current_object.name
        obj = self.current_object
        obj_dict = self.soi_objects[cls_name]

        old_value = obj.single_attr_input_value(attr_name, index)
        if new_value == old_value:
            print("value not changed")
            return old_value

        if attr_name == "name":
            if new_value in obj_dict:
                raise DBExistingNameError("Name {} already exists".format(new_value),
                                          AttributeKey(cls_name, obj_name, attr_name))
            if self.current_object_is_new:
                self.current_object.change_single_attrib_value("name", new_value)
            else:
                self.rename_object(cls_name, obj_name, new_value)
        else:
            if self.current_object_is_new:
                self.current_object.change_single_attrib_value(attr_name, new_value, index)
            else:
                self.change_attrib_value_existing(attr_name, new_value, index)
        return old_value

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
        obj.change_single_attrib_value("name", new_obj_name)

        # 4. rename obj in dependent attributes
        for dependent_obj_tuple in self.to_child_attribute_dict[cls_name][new_obj_name]:
            dependent_obj, attr_name, index = dependent_obj_tuple
            dependent_obj.change_single_attrib_value(attr_name, new_obj_name, index)

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
                        links = route_.cycle_links
                        raise DBCycleError("Cycle in dependencies was found",
                                           [self.link_to_attribute_dict[link] for link in links])
            return link_dg, (self_node.ni_pu, parent_node.ni_nd)

    def change_attrib_value_existing(self, attr_name: str, new_value: str, index: int):
        cls_name = self.current_object.__class__.__name__
        obj_name = self.current_object.name
        obj = self.current_object
        descr = getattr(obj.__class__, attr_name)
        if isinstance(descr, StationObjectDescriptor):
            contains_cls_name = descr.contains_cls_name
            try_result = self.try_change_attr_value(cls_name, obj_name, attr_name, new_value, index, contains_cls_name)
            if not (try_result is None):
                old_link, new_ni_tuple = try_result
                self.link_to_attribute_dict.pop(old_link)
                self.dg.disconnect_inf_handling(*old_link.ni_s)
                new_link = self.dg.connect_inf_handling(*new_ni_tuple)
                self.to_parent_link_dict[cls_name][obj_name][attr_name][index] = new_link
                self.link_to_attribute_dict[new_link] = AttributeKey(cls_name, obj_name, attr_name, index)
        obj.change_single_attrib_value(attr_name, new_value, index)


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
        deleted = r.delete_object("AxisSOI", "Axis_2")
        print(deleted)
        print([obj.name for obj in r.rectify_dg()])
        r.recover_objects(deleted)
        print([obj.name for obj in r.rectify_dg()])
