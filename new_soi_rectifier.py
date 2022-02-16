from __future__ import annotations
from typing import Union, Iterable, Optional
from collections import OrderedDict, defaultdict

from cell_object import CellObject
from two_sided_graph import OneComponentTwoSidedPG, PolarNode
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

        # current object state
        self.current_object: Optional[StationObjectImage] = None
        self.current_object_is_new: bool = True

        self.reset_storages()

    def reset_storages(self):
        self.soi_objects: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)
        self.soi_objects["CoordinateSystemSOI"][GLOBAL_CS_NAME] = self.gcs
        self.dg = OneComponentTwoSidedPG()
        self.dirty_dg: Optional[OneComponentTwoSidedPG] = None
        self.gcs_node = self.dg.insert_node()
        gcs_cell = ObjNodeCell("CoordinateSystemSOI", GLOBAL_CS_NAME)
        self.gcs_node.append_cell_obj(gcs_cell)
        self.to_self_node_dict: defaultdict[str, dict[str, tuple[PolarNode, ObjNodeCell]]] = defaultdict(dict)
        self.to_self_node_dict["CoordinateSystemSOI"][GLOBAL_CS_NAME] = self.gcs_node, gcs_cell
        self.to_child_attribute_dict: defaultdict[str, defaultdict[str, list[tuple]]] = \
            defaultdict(lambda: defaultdict(list))

    def reload_from_dict(self, od: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]]):
        self.reset_storages()

        # Stage 1 - names, nodes and their cells initialization
        for cls_name in od:
            for obj_name, obj in od[cls_name].items():
                if obj_name == GLOBAL_CS_NAME:
                    continue
                self.soi_objects[cls_name][obj_name] = obj
                obj: StationObjectImage
                node = self.dg.insert_node()
                cell = ObjNodeCell(cls_name, obj_name)
                node.append_cell_obj(cell)
                self.to_self_node_dict[cls_name][obj_name] = node, cell

        # Stage 2 - evaluate soi-descriptor odicts
        for cls in StationObjectImage.__subclasses__():
            for attr_name in cls.__dict__:
                if (not attr_name.startswith("__")) and \
                        isinstance(descr := getattr(cls, attr_name), StationObjectDescriptor):
                    descr.obj_dict = self.soi_objects[descr.contains_cls_name]

        # Stage 3 - nodes connections relied on formal requirements to attributes
        for cls_name in od:
            for obj_name, obj in od[cls_name].items():
                if obj_name == GLOBAL_CS_NAME:
                    continue
                obj: StationObjectImage
                for attr_name in obj.active_attrs:
                    if (not attr_name.startswith("__")) and \
                            isinstance(descr := getattr(obj.__class__, attr_name), StationObjectDescriptor):
                        contains_cls_name = descr.contains_cls_name
                        obj_names_dict = self.soi_objects[contains_cls_name]
                        attr_prop_values = getattr(obj, attr_name)
                        if isinstance(attr_prop_values, AttribProperties):
                            attr_prop_values = [attr_prop_values]
                        attr_prop_values: list[AttribProperties]
                        for i, attr_prop in enumerate(attr_prop_values):
                            if len(attr_prop_values) == 1:
                                i = -1
                            parent_name = attr_prop.last_input_value
                            if parent_name in obj_names_dict:
                                self_node = self.to_self_node_dict[cls_name][obj_name][0]
                                parent_node = self.to_self_node_dict[contains_cls_name][parent_name][0]
                                self.to_child_attribute_dict[contains_cls_name][parent_name].append((obj, attr_name, i))
                                self.dg.connect_inf_handling(self_node.ni_pu, parent_node.ni_nd)

        # Stage 4 - copy to dirty graph
        self.dirty_dg = self.dg.copy_part()

        # Stage 5 - check cycles
        self.full_check_cycle_dg()

        # Stage 6 - obj attributes evaluations for StationObjectDescriptor
        for cls_name in self.soi_objects:
            for obj_name in self.soi_objects[cls_name]:
                obj = self.soi_objects[cls_name][obj_name]
                if obj_name != GLOBAL_CS_NAME:
                    for attr_name in obj.active_attrs:
                        descr = getattr(obj.__class__, attr_name)
                        if isinstance(descr, StationObjectDescriptor):
                            is_list = descr.is_list
                            if not is_list:
                                ap: AttribProperties = getattr(obj, attr_name)
                                setattr(obj, attr_name, ap.last_input_value)
                            else:
                                ap_list: list[AttribProperties] = getattr(obj, attr_name)
                                setattr(obj, attr_name, ([ap.last_input_value for ap in ap_list],
                                                         IndexManagementCommand(command="set_list")))

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
        # 1. input checks
        obj_dict = self.soi_objects[cls_name]
        if new_obj_name == old_obj_name:
            return
        if new_obj_name in obj_dict:
            raise DBExistingNameError(cls_name, old_obj_name, "name", "Name {} already exists".format(new_obj_name))

        # 2. rename obj in dependent attributes
        for obj_tuple in self.to_child_attribute_dict[cls_name][old_obj_name]:
            obj, attr_name, i = obj_tuple
            if i == -1:
                setattr(obj, attr_name, new_obj_name)
            else:
                setattr(obj, attr_name, (new_obj_name, IndexManagementCommand(command="set_index", index=i)))

        # 3. rename obj in dicts and in cell
        obj_dict[new_obj_name] = obj_dict[old_obj_name]
        obj_dict.pop(old_obj_name)

        cell = self.to_self_node_dict[cls_name][old_obj_name][1]
        cell.obj_name = new_obj_name

        self.to_self_node_dict[cls_name][new_obj_name] = self.to_self_node_dict[cls_name][old_obj_name]
        self.to_self_node_dict[cls_name].pop(old_obj_name)

        self.to_child_attribute_dict[cls_name][new_obj_name] = self.to_child_attribute_dict[cls_name][old_obj_name]
        self.to_child_attribute_dict[cls_name].pop(old_obj_name)

    def create_new_object(self, cls_name: str):
        """ clean operation """
        self.current_object: StationObjectImage = eval(cls_name)()
        self.current_object_is_new = True

    def select_current_object(self, cls_name: str, obj_name: str):
        """ clean operation """
        self.current_object = self.soi_objects[cls_name][obj_name]
        self.current_object_is_new = False

    def push_new_object(self):
        co = self.current_object
        self.soi_objects[co.__class__.__name__][co.name] = co

    def change_attrib_value(self, a):
        """ dirty operation """
        pass


if __name__ == "__main__":
    test_1 = True
    if test_1:
        r = StorageDG()
        # print("r")
        config_objs = read_station_config("station_in_config")
        # print("read_station_config")
        r.reload_from_dict(config_objs)
        print(len(r.dg.links))
        print("delete : ", r.delete_object("AxisSOI", "Axis_2"))
        print(len(r.dg.links))
        print(r.dg.links)
        print(r.dg.nodes)
        # sec_dg = r.dg.copy_part()
        # print(len(sec_dg.links))
        # print([obj.name for obj in r.rectify_dg()])
        # print(r.dependent_objects_names("PointSOI", "Point_18"))
        # print(r.rename_object("PointSOI", "Point_18", "Point_180"))
        # print(r.rectify_dg())
        # print(r.dependent_objects_names("PointSOI", "Point_18"))
        # print(r.soi_objects["LineSOI"]["Line_7"].points)
