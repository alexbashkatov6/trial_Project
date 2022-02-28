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
from attribute_object_key import AttributeKey, ObjectKey

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


class SOIStorage:
    def __init__(self):
        """ docstring """
        """ base data structures """
        self.soi_objects: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)
        self.gcs = CoordinateSystemSOI()
        self.gcs.name = GLOBAL_CS_NAME

        """ init operations """
        self.init_soi_classes()
        self.bind_descriptors()
        self.reset_clean_storages()

    @property
    def soi_objects_no_gcs(self) -> DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]]:
        result = DefaultOrderedDict(OrderedDict)
        for cls_name in self.soi_objects:
            for obj_name, obj in self.soi_objects[cls_name].items():
                if obj_name == GLOBAL_CS_NAME:
                    continue
                result[cls_name][obj_name] = obj
        return result

    def init_soi_classes(self):
        for cls in StationObjectImage.__subclasses__():
            self.soi_objects[cls.__name__] = OrderedDict()

    def bind_descriptors(self):
        for cls in StationObjectImage.__subclasses__():
            for attr_name in cls.__dict__:
                if not attr_name.startswith("__"):
                    if isinstance(descr := getattr(cls, attr_name), (StationObjectDescriptor, NameDescriptor)):
                        descr.obj_dict = self.soi_objects[descr.contains_cls_name]

    def reset_clean_storages(self):
        for cls_name in self.soi_objects:
            self.soi_objects[cls_name].clear()
        self.soi_objects["CoordinateSystem"][GLOBAL_CS_NAME] = self.gcs

    def add_obj_to_soi(self, obj: StationObjectImage):
        cls_name = obj.__class__.__name__
        obj_name = obj.name
        self.soi_objects[cls_name][obj_name] = obj


class SOIDependenceGraph:
    def __init__(self):
        """ docstring """
        """ base data structures """
        self.node_to_obj_key: dict[PolarNode, ObjectKey] = {}
        self.link_to_attribute_key: dict[Link, AttributeKey] = {}

        """ gcs node init """
        self.dg = OneComponentTwoSidedPG()
        self.gcs_node = self.dg.insert_node()
        self.node_to_obj_key[self.gcs_node] = ObjectKey("CoordinateSystem", GLOBAL_CS_NAME)

        """ init operations """
        self.reset_clean_storages()

    @property
    def attribute_key_to_link(self) -> dict[AttributeKey, Link]:
        return {val: key for (key, val) in self.link_to_attribute_key.items()}

    @property
    def obj_key_to_node(self) -> dict[ObjectKey, PolarNode]:
        return {val: key for (key, val) in self.node_to_obj_key.items()}

    @property
    def parent_obj_key_to_child_attributes_keys(self) -> dict[ObjectKey, set[AttributeKey]]:
        result = {}
        for node in self.dg.not_inf_nodes:
            inf_node_nd_links = self.dg.inf_nd.ni_pu.links
            result[self.node_to_obj_key[node]] = {self.link_to_attribute_key[link] for link in node.ni_nd.links
                                                  if link not in inf_node_nd_links}
        return result

    def reset_clean_storages(self):
        self.node_to_obj_key.clear()
        self.link_to_attribute_key.clear()

        self.dg = OneComponentTwoSidedPG()
        self.gcs_node = self.dg.insert_node()
        self.node_to_obj_key[self.gcs_node] = ObjectKey("CoordinateSystem", GLOBAL_CS_NAME)

    def init_clean_nodes(self, obj_keys: list[ObjectKey]):
        self.reset_clean_storages()
        for obj_key in obj_keys:
            if obj_key == self.node_to_obj_key[self.gcs_node]:
                continue
            self.init_obj_node_dg(obj_key)

    def init_obj_node_dg(self, obj_key: ObjectKey):
        node = self.dg.insert_node()
        self.node_to_obj_key[node] = obj_key

    def rectify_dg(self) -> list[ObjectKey]:
        nodes: list[PolarNode] = list(flatten(self.dg.longest_coverage()))[1:]  # without Global CS
        return [self.node_to_obj_key[node] for node in nodes]

    def dependent_objects_keys(self, obj_key: ObjectKey) -> list[ObjectKey]:
        self_node = self.obj_key_to_node[obj_key]
        dependent_nodes = list(flatten(self.dg.longest_coverage(self_node.ni_nd)))
        return [self.node_to_obj_key[node] for node in dependent_nodes]

    def divide_remain_delete_object(self, obj_key: ObjectKey) -> tuple[list[ObjectKey], list[ObjectKey]]:
        dependent_objects_keys = self.dependent_objects_keys(obj_key)
        remain_soi_object_keys: list[ObjectKey] = []
        del_soi_object_keys: list[ObjectKey] = []
        for node in self.dg.not_inf_nodes:
            obj_key = self.node_to_obj_key[node]
            if obj_key in dependent_objects_keys:
                del_soi_object_keys.append(obj_key)
            else:
                remain_soi_object_keys.append(obj_key)
        return remain_soi_object_keys, del_soi_object_keys

    def make_dependence(self, parent_obj_key: ObjectKey, child_obj_key: ObjectKey, attr_key: AttributeKey):
        new_link = self.dg.connect_inf_handling(self.obj_key_to_node[parent_obj_key].ni_nd,
                                                self.obj_key_to_node[child_obj_key].ni_pu)
        self.link_to_attribute_key[new_link] = attr_key
        self.check_new_cycles(parent_obj_key)

    def remove_dependence(self, attr_key: AttributeKey):
        self.dg.disconnect_inf_handling(*self.attribute_key_to_link[attr_key].ni_s)

    def check_new_cycles(self, obj_key: ObjectKey):
        node = self.obj_key_to_node[obj_key]
        routes = self.dg.walk(node.ni_nd)
        for route in routes:
            if route.is_cycle:
                raise DBCycleError("Cycle")


if __name__ == "__main__":
    test_1 = True
    if test_1:
        # print("r")
        r = SOIDependenceGraph()
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
        deleted = r.divide_remain_delete_object("AxisSOI", "Axis_2")
        print(deleted)
        print([obj.name for obj in r.rectify_dg()])
        r.recover_objects(deleted)
        print([obj.name for obj in r.rectify_dg()])
