from __future__ import annotations
from typing import Union, Iterable
from collections import OrderedDict, defaultdict

from cell_object import CellObject
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Link
from default_ordered_dict import DefaultOrderedDict
from new_soi_objects import StationObjectImage, CoordinateSystemSOI, StationObjectDescriptor, AttribProperties, \
    IndexManagementCommand
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


# class AttrLinkCell(CellObject):
#     def __init__(self, obj_name: str, attr_name: str):
#         self.obj_name = obj_name
#         self.attr_name = attr_name


class Rectifier:
    def __init__(self):
        self.gcs = CoordinateSystemSOI()
        self.gcs.name = GLOBAL_CS_NAME
        self.reset_storages()

    def reset_storages(self):
        self.soi_objects: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)
        self.soi_objects["CoordinateSystemSOI"][GLOBAL_CS_NAME] = self.gcs
        self.dg = OneComponentTwoSidedPG()
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

        # Stage 4 - check cycles
        self.full_check_cycle_dg()

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

    def rectify_dg(self) -> list[str]:
        nodes: list[PolarNode] = list(flatten(self.dg.longest_coverage()))[1:]  # without Global CS
        return [element_cell_by_type(node, ObjNodeCell).obj_name for node in nodes]

    def dependent_objects_names(self, cls_name: str, obj_name: str) -> list[str]:
        self_node = self.to_self_node_dict[cls_name][obj_name][0]
        dependent_nodes = list(flatten(self.dg.shortest_coverage(self_node.ni_nd)))
        return [element_cell_by_type(node, ObjNodeCell).obj_name for node in dependent_nodes]

    def rename_object(self, cls_name: str, old_obj_name: str, new_obj_name: str):
        # 1. rename obj in soi-dict and in cell
        obj_dict = self.soi_objects[cls_name]
        if new_obj_name == old_obj_name:
            return
        if new_obj_name in obj_dict:
            raise DBExistingNameError(cls_name, old_obj_name, "name", "Name {} already exists".format(new_obj_name))
        obj_dict[new_obj_name] = obj_dict[old_obj_name]
        obj_dict.pop(old_obj_name)
        cell = self.to_self_node_dict[cls_name][old_obj_name][1]
        cell.obj_name = new_obj_name
        self.to_self_node_dict[cls_name][new_obj_name] = self.to_self_node_dict[cls_name][old_obj_name]
        self.to_self_node_dict[cls_name].pop(old_obj_name)

        # 2. rename obj in dependent attributes
        for obj_tuple in self.to_child_attribute_dict[cls_name][old_obj_name]:
            obj, attr_name, i = obj_tuple
            if i == -1:
                setattr(obj, attr_name, new_obj_name)
            else:
                setattr(obj, attr_name, (new_obj_name, IndexManagementCommand(command="set_index", index=i)))
        self.to_child_attribute_dict[cls_name][new_obj_name] = self.to_child_attribute_dict[cls_name][old_obj_name]
        self.to_child_attribute_dict[cls_name].pop(old_obj_name)


if __name__ == "__main__":
    test_1 = True
    if test_1:
        r = Rectifier()
        config_objs = read_station_config("station_in_config")
        r.reload_from_dict(config_objs)
        print(len(r.dg.links))
        print(r.rectify_dg())
        print(r.dependent_objects_names("PointSOI", "Point_18"))
        print(r.rename_object("PointSOI", "Point_18", "Point_180"))
        print(r.rectify_dg())
        print(r.dependent_objects_names("PointSOI", "Point_180"))
        print(r.soi_objects["LineSOI"]["Line_7"].points)
