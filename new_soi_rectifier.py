from __future__ import annotations
from typing import Union, Iterable
from collections import OrderedDict, defaultdict

from cell_object import CellObject
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Link
from default_ordered_dict import DefaultOrderedDict
from new_soi_objects import StationObjectImage, CoordinateSystemSOI, StationObjectDescriptor, AttribProperties
from soi_files_handler import read_station_config

from config_names import GLOBAL_CS_NAME


class AttributeEvaluateError(Exception):
    pass


class AERequiredAttributeError(AttributeEvaluateError):
    pass


class AEObjectNotFoundError(AttributeEvaluateError):
    pass


class AETypeAttributeError(AttributeEvaluateError):
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
        self.gcs_node.append_cell_obj(ObjNodeCell("CoordinateSystemSOI", GLOBAL_CS_NAME))
        self.to_self_node_dict: defaultdict[str, dict[str, PolarNode]] = defaultdict(dict)
        self.to_self_node_dict["CoordinateSystemSOI"][GLOBAL_CS_NAME] = self.gcs_node
        self.to_parent_node_dict: defaultdict[str, defaultdict[tuple[str, int], dict[str, PolarNode]]] = \
            defaultdict(lambda: defaultdict(dict))

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
                node.append_cell_obj(ObjNodeCell(cls_name, obj_name))
                self.to_self_node_dict[cls_name][obj_name] = node

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
                        contains_class_name = descr.contains_cls_name
                        obj_names_dict = self.soi_objects[contains_class_name]
                        attr_prop_values = getattr(obj, attr_name)
                        if isinstance(attr_prop_values, AttribProperties):
                            attr_prop_values = [attr_prop_values]
                        attr_prop_values: list[AttribProperties]
                        for i, attr_prop in enumerate(attr_prop_values):
                            if len(attr_prop_values) == 1:
                                i = -1
                            parent_name = attr_prop.last_input_value
                            if parent_name in obj_names_dict:
                                self_node = self.to_self_node_dict[cls_name][obj_name]
                                parent_node = self.to_self_node_dict[contains_class_name][parent_name]
                                self.to_parent_node_dict[cls_name][obj_name][(attr_name, i)] = parent_node
                                self.dg.connect_inf_handling(self_node.ni_pu, parent_node.ni_nd)


if __name__ == "__main__":
    test_1 = True
    if test_1:
        r = Rectifier()
        config_objs = read_station_config("station_in_config")
        r.reload_from_dict(config_objs)
        print(len(r.dg.links))
