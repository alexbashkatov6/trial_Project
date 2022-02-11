from __future__ import annotations
from typing import Union
from collections import OrderedDict

from cell_object import CellObject
from two_sided_graph import OneComponentTwoSidedPG, PolarNode
from default_ordered_dict import DefaultOrderedDict
from new_soi_objects import StationObjectImage, CoordinateSystemSOI, AxisSOI, PointSOI, LineSOI, \
    LightSOI, RailPointSOI, BorderSOI, SectionSOI
from soi_files_handler import read_station_config
from enums_images import CEDependence, CEBool, CEAxisCreationMethod, CEAxisOrLine, CELightRouteType, CELightStickType, \
    CEBorderType, CELightColor

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


class AttrLinkCell(CellObject):
    def __init__(self, obj_name: str, attr_name: str):
        self.obj_name = obj_name
        self.attr_name = attr_name


class Rectifier:
    def __init__(self):
        self.gcs = CoordinateSystemSOI()
        self.gcs.name = GLOBAL_CS_NAME
        self.reset_storages()

    def reset_storages(self):
        self.soi_objects: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)
        self.soi_objects["CoordinateSystemSOI"][GLOBAL_CS_NAME] = self.gcs
        self.dg = OneComponentTwoSidedPG()

    def reload_from_dict(self, od: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]]):
        self.reset_storages()

        # Stage 1 - names, nodes and their cells initialization;
        for cls_name in od:
            for obj_name, obj in od[cls_name].items():
                if obj_name == GLOBAL_CS_NAME:
                    continue
                self.soi_objects[cls_name][obj_name] = obj
                obj: StationObjectImage
                node = self.dg.insert_node()
                node.append_cell_obj(ObjNodeCell(cls_name, obj_name))

        # Stage 2 - evaluate descriptor connections
        CoordinateSystemSOI.cs_relative_to.possible_values = self.soi_objects["CoordinateSystemSOI"].keys()
        CoordinateSystemSOI.dependence.possible_values = CEDependence.possible_values
        CoordinateSystemSOI.co_x.possible_values = CEBool.possible_values
        CoordinateSystemSOI.co_y.possible_values = CEBool.possible_values

        AxisSOI.cs_relative_to.possible_values = self.soi_objects["CoordinateSystemSOI"].keys()
        AxisSOI.creation_method.possible_values = CEAxisCreationMethod.possible_values
        AxisSOI.center_point.possible_values = self.soi_objects["PointSOI"].keys()

        PointSOI.on.possible_values = CEAxisOrLine.possible_values
        PointSOI.axis.possible_values = self.soi_objects["AxisSOI"]
        PointSOI.line.possible_values = self.soi_objects["LineSOI"]
        PointSOI.cs_relative_to.possible_values = self.soi_objects["CoordinateSystemSOI"].keys()

        LineSOI.points.possible_values = self.soi_objects["PointSOI"].keys()

        LightSOI.light_route_type.possible_values = CELightRouteType.possible_values
        LightSOI.center_point.possible_values = self.soi_objects["PointSOI"].keys()
        LightSOI.direct_point.possible_values = self.soi_objects["PointSOI"].keys()
        LightSOI.colors.possible_values = CELightColor.possible_values
        LightSOI.light_stick_type.possible_values = CELightStickType.possible_values

        RailPointSOI.center_point.possible_values = self.soi_objects["PointSOI"].keys()
        RailPointSOI.dir_plus_point.possible_values = self.soi_objects["PointSOI"].keys()
        RailPointSOI.dir_minus_point.possible_values = self.soi_objects["PointSOI"].keys()

        BorderSOI.point.possible_values = self.soi_objects["PointSOI"].keys()
        BorderSOI.border_type.possible_values = CEBorderType.possible_values

        SectionSOI.border_points.possible_values = self.soi_objects["PointSOI"].keys()

        # Stage 3 - check formal requirements to attributes, nodes connections and link cells initialization
        for cls_name in od:
            for obj_name, obj in od[cls_name].items():
                if obj_name == GLOBAL_CS_NAME:
                    continue
                obj: StationObjectImage
                for attr_name in obj.active_attrs:
                    pass


if __name__ == "__main__":
    test_1 = True
    if test_1:
        r = Rectifier()
        config_objs = read_station_config("station_in_config")
        r.reload_from_dict(config_objs)
