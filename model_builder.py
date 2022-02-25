from __future__ import annotations
from collections import OrderedDict
import math

from enums_images import CEAxisCreationMethod, CEAxisOrLine, CELightRouteType, CEBorderType, CESectionType
from soi_objects import StationObjectImage, CoordinateSystemSOI, AxisSOI, PointSOI, LineSOI, \
    LightSOI, RailPointSOI, BorderSOI, SectionSOI
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Route, NodeInterface
from cell_object import CellObject
from graphical_object import Point2D, Angle, Line2D, BoundedCurve, lines_intersection, evaluate_vector, \
    ParallelLinesException, EquivalentLinesException, PointsEqualException, OutBorderException
from cell_access_functions import NotFoundCellError, element_cell_by_type, all_cells_of_type, find_cell_name
from rail_route import RailRoute
from xml_formation import form_rail_routes_xml
from mo_objects import ModelObject, CoordinateSystemMO, AxisMO, PointMO, LineMO, LightMO, RailPointMO, BorderMO, \
    SectionMO
from default_ordered_dict import DefaultOrderedDict
from attribute_data import AttributeErrorData

from config_names import GLOBAL_CS_NAME


class ModelBuildError(Exception):
    pass


class MBSkeletonError(ModelBuildError):
    pass


class MBEquipmentError(ModelBuildError):
    pass


class PointCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class RailPointCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class BorderCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class LightCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class IsolatedSectionCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class LineCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class LengthCell(CellObject):
    def __init__(self, length: float):
        self.length = length


class RailPointDirectionCell(CellObject):
    def __init__(self, direction: str):
        self.direction = direction


class ModelBuilder:
    def __init__(self):
        self.mo_gcs = CoordinateSystemMO()
        self.mo_gcs.name = GLOBAL_CS_NAME
        self.mo_dict: DefaultOrderedDict[str, OrderedDict[str, ModelObject]] = DefaultOrderedDict(OrderedDict)

    def changed_attrib(self, cls_name, obj_name):
        pass
