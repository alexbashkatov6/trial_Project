from __future__ import annotations
from typing import Type, Optional, Union, Iterable
from collections import OrderedDict, Counter
from copy import copy
import pandas as pd
import os
from abc import abstractmethod
from numbers import Real
import math
import re
import xml.etree.ElementTree as ElTr
import xml.dom.minidom

from custom_enum import CustomEnum
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Element, Route
from cell_object import CellObject
from extended_itertools import single_element, recursive_map, flatten, EINotFoundError, EIManyFoundError
from graphical_object import Point2D, Angle, Line2D, BoundedCurve, lines_intersection, evaluate_vector, \
    ParallelLinesException, EquivalentLinesException, PointsEqualException, OutBorderException

GLOBAL_CS_NAME = "GlobalCS"
STATION_OUT_CONFIG_FOLDER = "station_out_config"
STATION_IN_CONFIG_FOLDER = "station_in_config"

# -------------------------        OBJECT IMAGES CLASSES        ------------------------- #


# ------------        EXCEPTIONS        ------------ #

class BuildSkeletonError(Exception):
    pass


class BuildEquipmentError(Exception):
    pass


class NotImplementedCoError(Exception):
    pass


class RepeatingPointsCOError(Exception):
    pass


class LineDefinitionByPointsCOError(Exception):
    pass


class RequiredAttributeNotDefinedCOError(Exception):
    pass


class PicketCoordinateParsingCoError(Exception):
    pass


class ObjectNotFoundCoError(Exception):
    pass


class NoNameCoError(Exception):
    pass


class ExistingNameCoError(Exception):
    pass


class TypeCoError(Exception):
    pass


class SyntaxCoError(Exception):
    pass


class SemanticCoError(Exception):
    pass


class CycleError(Exception):
    pass


# ------------        ENUMS        ------------ #


class CECommand(CustomEnum):
    load_config = 0
    create_object = 1
    rename_object = 2
    change_attrib_value = 3
    delete_object = 4


class CEDependence(CustomEnum):
    dependent = 0
    independent = 1


class CEBool(CustomEnum):
    false = 0
    true = 1


class CEAxisCreationMethod(CustomEnum):
    translational = 0
    rotational = 1


class CEAxisOrLine(CustomEnum):
    axis = 0
    line = 1


class CELightRouteType(CustomEnum):
    train = 0
    shunt = 1


class CELightStickType(CustomEnum):
    mast = 0
    dwarf = 1


class CELightColor(CustomEnum):
    dark = 0
    red = 1
    blue = 2
    white = 3
    yellow = 4
    green = 5


class CEBorderType(CustomEnum):
    standoff = 0
    ab = 1
    pab = 2


# ------------        IMAGES COMMON AGGREGATE ATTRS        ------------ #


class SOIAttrSeqTemplate:
    def __get__(self, instance, owner) -> list[str]:

        if owner == CoordinateSystemSOI:
            return [x.name for x in
                    [CoordinateSystemSOI.cs_relative_to,
                     CoordinateSystemSOI.dependence,
                     CoordinateSystemSOI.x,
                     CoordinateSystemSOI.co_x,
                     CoordinateSystemSOI.co_y]]

        if owner == AxisSOI:
            return [x.name for x in
                    [AxisSOI.cs_relative_to,
                     AxisSOI.creation_method,
                     AxisSOI.y,
                     AxisSOI.center_point,
                     AxisSOI.alpha]]

        if owner == PointSOI:
            return [x.name for x in
                    [PointSOI.on,
                     PointSOI.axis,
                     PointSOI.line,
                     PointSOI.cs_relative_to,
                     PointSOI.x]]

        if owner == LineSOI:
            return [x.name for x in
                    [LineSOI.points]]

        if owner == LightSOI:
            return [x.name for x in
                    [LightSOI.light_route_type,
                     LightSOI.center_point,
                     LightSOI.direct_point,
                     LightSOI.colors,
                     LightSOI.light_stick_type]]

        if owner == RailPointSOI:
            return [x.name for x in
                    [RailPointSOI.center_point,
                     RailPointSOI.dir_plus_point,
                     RailPointSOI.dir_minus_point]]

        if owner == BorderSOI:
            return [x.name for x in
                    [BorderSOI.point,
                     BorderSOI.border_type]]

        if owner == SectionSOI:
            return [x.name for x in
                    [SectionSOI.border_points]]

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class SOIActiveAttrs:
    def __get__(self, instance, owner):
        assert instance, "Only for instance"
        instance: StationObjectImage
        instance._active_attrs = instance.attr_sequence_template

        if owner == CoordinateSystemSOI:
            instance: CoordinateSystemSOI
            if instance.dependence == CEDependence.independent:
                instance._active_attrs.remove(CoordinateSystemSOI.x.name)
                instance._active_attrs.remove(CoordinateSystemSOI.co_x.name)
                instance._active_attrs.remove(CoordinateSystemSOI.co_y.name)

        if owner == AxisSOI:
            instance: AxisSOI
            if instance.creation_method == CEAxisCreationMethod.rotational:
                instance._active_attrs.remove(AxisSOI.y.name)
            else:
                instance._active_attrs.remove(AxisSOI.alpha.name)
                instance._active_attrs.remove(AxisSOI.center_point.name)

        if owner == PointSOI:
            instance: PointSOI
            if instance.on == CEAxisOrLine.axis:
                instance._active_attrs.remove(PointSOI.line.name)
            else:
                instance._active_attrs.remove(PointSOI.axis.name)

        return instance._active_attrs

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class SOIListPossibleValues:
    def __get__(self, instance, owner):
        if instance is None:
            result = OrderedDict()
            for attr_ in owner.attr_sequence_template:
                attrib = getattr(owner, attr_)
                if attrib.enum:
                    result[attr_] = attrib.enum.possible_values
                else:
                    result[attr_] = []
        else:
            instance: StationObjectImage
            result = OrderedDict()
            for active_attr in instance.active_attrs:
                attrib = getattr(instance, active_attr)
                if isinstance(attrib, CustomEnum):
                    result[active_attr] = attrib.possible_values
                else:
                    result[active_attr] = []
        return result

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class SOIListValues:
    def __get__(self, instance, owner):
        assert instance, "Only for instance"
        instance: StationObjectImage
        result = OrderedDict()
        for active_attr in instance.active_attrs:
            result[active_attr] = getattr(instance, active_attr)
        return result

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


def predict_name(instance: StationObjectImage) -> str:
    i = 0
    cls_name = instance.__class__.__name__
    while True:
        i += 1
        predicted_name = "{}_{}".format(cls_name, i)
        if predicted_name not in SOIS.names_list:
            return predicted_name


class SOIName:
    def __get__(self, instance, owner):
        assert instance, "Only for instance"
        return getattr(instance, "_name")

    def __set__(self, instance, value: str):
        instance._name = value


# ------------        BASE ATTRIBUTE DESCRIPTOR        ------------ #


class BaseAttrDescriptor:

    def __init__(self, expected_type: Union[str, Type[CustomEnum]] = None):
        self.enum = None
        self.str_expected_type: str = ""
        self.expected_type = None
        self.is_complex_type = False
        if expected_type:
            if expected_type == "complex_type":
                self.is_complex_type = True
            elif isinstance(expected_type, str):
                self.str_expected_type: str = expected_type  # eval because Py-class cannot directly contain its name
            else:
                self.enum = expected_type

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if not instance:
            return self
        elif hasattr(instance, "_"+self.name) and not (getattr(instance, "_"+self.name) is None):
            return getattr(instance, "_"+self.name)
        elif hasattr(instance, "_predicted_"+self.name):
            return getattr(instance, "_predicted_"+self.name)
        else:
            return None

    def __set__(self, instance: StationObjectImage, value: str):
        value = value.strip()
        setattr(instance, "_str_"+self.name, value)

        if self.enum:
            setattr(instance, "_" + self.name, self.enum(value))
        elif self.is_complex_type:
            return
        elif self.str_expected_type:
            self.expected_type = eval(self.str_expected_type)  # eval because Py-class cannot directly contain its name
        else:
            assert False, "No requirements found"


# ------------        PARTIAL ATTRIBUTE DESCRIPTORS        ------------ #


class CsCsRelTo(BaseAttrDescriptor):
    pass


class CsDepend(BaseAttrDescriptor):
    pass


class CsX(BaseAttrDescriptor):
    pass


class CsY(BaseAttrDescriptor):
    pass


class CsAlpha(BaseAttrDescriptor):
    pass


class CsCoX(BaseAttrDescriptor):
    pass


class CsCoY(BaseAttrDescriptor):
    pass


class AxCsRelTo(BaseAttrDescriptor):
    pass


class AxCrtMethod(BaseAttrDescriptor):
    pass


class AxY(BaseAttrDescriptor):
    pass


class AxCenterPoint(BaseAttrDescriptor):
    pass


class AxAlpha(BaseAttrDescriptor):
    pass


class PntOn(BaseAttrDescriptor):
    pass


class PntAxis(BaseAttrDescriptor):
    pass


class PntLine(BaseAttrDescriptor):
    pass


class PntCsRelTo(BaseAttrDescriptor):
    pass


class PntX(BaseAttrDescriptor):
    pass


class LinePoints(BaseAttrDescriptor):
    pass


class LightRouteType(BaseAttrDescriptor):
    pass


class LightStickType(BaseAttrDescriptor):
    pass


class LightCenterPoint(BaseAttrDescriptor):
    pass


class LightDirectionPoint(BaseAttrDescriptor):
    pass


class LightColors(BaseAttrDescriptor):
    pass


class RailPCenterPoint(BaseAttrDescriptor):
    pass


class RailPDirPlusPoint(BaseAttrDescriptor):
    pass


class RailPDirMinusPoint(BaseAttrDescriptor):
    pass


class BorderPoint(BaseAttrDescriptor):
    pass


class BorderType(BaseAttrDescriptor):
    pass


class SectBorderPoints(BaseAttrDescriptor):
    pass


# ------------        IMAGE OBJECTS CLASSES        ------------ #


class StationObjectImage:
    attr_sequence_template = SOIAttrSeqTemplate()
    active_attrs = SOIActiveAttrs()
    dict_possible_values = SOIListPossibleValues()
    dict_values = SOIListValues()
    name = SOIName()


class CoordinateSystemSOI(StationObjectImage):
    cs_relative_to = CsCsRelTo("CoordinateSystemSOI")
    dependence = CsDepend(CEDependence)
    x = CsX("int")
    co_x = CsCoX(CEBool)
    co_y = CsCoY(CEBool)


class AxisSOI(StationObjectImage):
    cs_relative_to = AxCsRelTo("CoordinateSystemSOI")
    creation_method = AxCrtMethod(CEAxisCreationMethod)
    y = AxY("int")
    center_point = AxCenterPoint("PointSOI")
    alpha = AxAlpha("int")


class PointSOI(StationObjectImage):
    on = PntOn(CEAxisOrLine)
    axis = PntAxis("AxisSOI")
    line = PntAxis("LineSOI")
    cs_relative_to = PntCsRelTo("CoordinateSystemSOI")
    x = PntX("complex_type")


class LineSOI(StationObjectImage):
    points = LinePoints("complex_type")


class LightSOI(StationObjectImage):
    light_route_type = LightRouteType(CELightRouteType)
    light_stick_type = LightStickType(CELightStickType)
    center_point = LightCenterPoint("PointSOI")
    direct_point = LightDirectionPoint("PointSOI")
    colors = LightColors("complex_type")


class RailPointSOI(StationObjectImage):
    center_point = RailPCenterPoint("PointSOI")
    dir_plus_point = RailPDirPlusPoint("PointSOI")
    dir_minus_point = RailPDirMinusPoint("PointSOI")


class BorderSOI(StationObjectImage):
    border_type = BorderType(CEBorderType)
    point = BorderPoint("PointSOI")


class SectionSOI(StationObjectImage):
    border_points = SectBorderPoints("complex_type")


# ------------        OTHER IMAGE CLASSES        ------------ #


class SOIEventHandler:
    pass


class SOIStorage:
    """ dumb class storage  """
    def __init__(self):
        self.class_objects: OrderedDict[str, OrderedDict[str, StationObjectImage]] = OrderedDict()
        for cls in StationObjectImage.__subclasses__():
            self.class_objects[cls.__name__] = OrderedDict()
        self.add_new_object(CoordinateSystemSOI(), GLOBAL_CS_NAME)

    def add_new_object(self, obj: StationObjectImage, name: str = None):
        if name:
            assert isinstance(obj, CoordinateSystemSOI) and (name == GLOBAL_CS_NAME), "Parameter only for GCS"
        else:
            name = obj.name
        self.class_objects[obj.__class__.__name__][name] = obj

    def get_object(self, name) -> StationObjectImage:
        for obj_dict in self.class_objects.values():
            if name in obj_dict:
                return obj_dict[name]
        assert False, "Name not found"

    @property
    def names_list(self) -> list[str]:
        nl = []
        for obj_dict in self.class_objects.values():
            nl.extend(obj_dict.keys())
        return nl


SOIS = SOIStorage()


class SOISelector:
    """ selected object editing """
    def __init__(self):
        self.current_object: Optional[StationObjectImage] = None
        self.is_new_object = True

    def create_empty_object(self, cls_name: str):
        assert cls_name in SOIS.class_objects, "Class name not found"
        cls: Type[StationObjectImage] = eval(cls_name)
        self.current_object: StationObjectImage = cls()
        self.is_new_object = True

    def edit_existing_object(self, obj_name: str):
        self.current_object = SOIS.get_object(obj_name)
        self.is_new_object = False

    def attrib_dict_possible_values(self):
        if not self.current_object:
            return OrderedDict()
        return self.current_object.dict_possible_values

    def attrib_dict_values(self):
        if not self.current_object:
            return OrderedDict()
        return self.current_object.dict_values


class ImageNameCell(CellObject):
    def __init__(self, name: str):
        self.name = name


def make_xlsx_templates(dir_name: str):
    folder = os.path.join(os.getcwd(), dir_name)
    for cls in StationObjectImage.__subclasses__():
        name_soi = cls.__name__
        name_del_soi = name_soi.replace("SOI", "")
        file = os.path.join(folder, "{}.xlsx".format(name_del_soi))
        max_possible_values_length = 0
        for val_list in cls.dict_possible_values.values():
            l_ = len(val_list)
            if l_ > max_possible_values_length:
                max_possible_values_length = l_
        od = OrderedDict([("name", [""]*max_possible_values_length)])
        for key, val_list in cls.dict_possible_values.items():
            val_list.extend([""]*(max_possible_values_length-len(val_list)))
            od[key] = val_list
        df = pd.DataFrame(data=od)
        df.to_excel(file, index=False)


def read_station_config(dir_name: str) -> list[StationObjectImage]:
    folder = os.path.join(os.getcwd(), dir_name)
    objs_ = []
    for cls in StationObjectImage.__subclasses__():
        name_soi = cls.__name__
        name_del_soi = name_soi.replace("SOI", "")
        file = os.path.join(folder, "{}.xlsx".format(name_del_soi))
        df: pd.DataFrame = pd.read_excel(file, dtype=str, keep_default_na=False)
        obj_dict_list: list[OrderedDict] = df.to_dict('records', OrderedDict)
        for obj_dict in obj_dict_list:
            new_obj = cls()
            for attr_name, attr_val in obj_dict.items():
                attr_name: str
                attr_val: str
                attr_name = attr_name.strip()
                attr_val = attr_val.strip()
                setattr(new_obj, attr_name, attr_val)  # can be raised custom enum exceptions
            objs_.append(new_obj)
    return objs_


# def get_object_by_name(name, obj_list) -> StationObjectImage:
#     for obj in obj_list:
#         if obj.name == name:
#             return obj
#     assert False, "Name not found"

# -------------------------        CELLS           -------------------- #


class PointCell(CellObject):
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


class CellError(Exception):
    pass


class NotFoundCellError(CellError):
    pass


class ManyFoundCellError(CellError):
    pass


# -------------------------        ACCESS FUNCTIONS           -------------------- #


def element_cell_by_type(el: Element, cls_name: str) -> CellObject:
    cls = eval(cls_name)
    found_cells = set()
    for cell in el.cell_objs:
        if isinstance(cell, cls):
            found_cells.add(cell)
    if not found_cells:
        raise NotFoundCellError("Not found")
    if len(found_cells) != 1:
        raise ManyFoundCellError("More then 1 cell found")
    return found_cells.pop()


def all_cells_of_type(elements: Iterable[Element], cls_name: str) -> dict[CellObject, Element]:
    result = {}
    for element in elements:
        try:
            co = element_cell_by_type(element, cls_name)
        except CellError:
            continue
        result[co] = element
    return result


def find_cell_name(elements: Iterable[Element], cls_name: str, name: str) -> Optional[tuple[CellObject, Element]]:
    cell_candidates = all_cells_of_type(elements, cls_name)
    try:
        co = single_element(lambda x: x.name == name, list(cell_candidates.keys()))
    except EINotFoundError:
        raise NotFoundCellError("Not found")
    except EIManyFoundError:
        raise ManyFoundCellError("More then 1 cell found")
    return co, cell_candidates[co]

# -------------------------        MODEL CLASSES           -------------------- #


class ModelObject:
    def __init__(self):
        self.name: str = ""


class CoordinateSystemMO(ModelObject):
    def __init__(self, base_cs: CoordinateSystemMO = None,
                 x: int = 0, co_x: bool = True, co_y: bool = True):
        super().__init__()
        self._base_cs = base_cs
        self._is_base = base_cs is None
        self._in_base_x = x
        self._in_base_co_x = co_x
        self._in_base_co_y = co_y

    @property
    def is_base(self) -> bool:
        return self._is_base

    @property
    def base_cs(self) -> CoordinateSystemMO:
        if self.is_base:
            return self
        return self._base_cs

    @property
    def in_base_x(self) -> int:
        return self._in_base_x

    @property
    def in_base_co_x(self) -> bool:
        return self._in_base_co_x

    @property
    def in_base_co_y(self) -> bool:
        return self._in_base_co_y

    @property
    def absolute_x(self) -> int:
        if self.is_base:
            return self.in_base_x
        return int(self.base_cs.absolute_x + self.in_base_x * (-0.5 + int(self.base_cs.absolute_co_x)) * 2)

    @property
    def absolute_co_x(self) -> bool:
        if self.is_base:
            return self.in_base_co_x
        return self.base_cs.absolute_co_x == self.in_base_co_x

    @property
    def absolute_co_y(self) -> bool:
        if self.is_base:
            return self.in_base_co_y
        return self.base_cs.absolute_co_y == self.in_base_co_y


class AxisMO(ModelObject):
    def __init__(self, line2D: Line2D):
        super().__init__()
        self.line2D = line2D
        self._points: list[PointMO] = []
        self._lines: list[LineMO] = []

    def append_point(self, point: PointMO):
        self._points.append(point)

    def append_line(self, line: LineMO):
        self._lines.append(line)

    @property
    def points(self):
        return sorted(self._points, key=lambda s: s.x)

    @property
    def lines(self):
        return self._lines

    @property
    def angle(self):
        return self.line2D.angle


class PointMO(ModelObject):
    def __init__(self, point2D: Point2D):
        super().__init__()
        self.point2D = point2D

    @property
    def x(self):
        return self.point2D.x

    @property
    def y(self):
        return self.point2D.y


class LineMO(ModelObject):
    def __init__(self, boundedCurves: list[BoundedCurve], points: list[PointMO] = None):
        super().__init__()
        self.boundedCurves = boundedCurves
        self._points: list[PointMO] = []
        self._axis = None
        if points:
            self._points = points

    def append_point(self, point: PointMO):
        self._points.append(point)

    @property
    def points(self):
        return sorted(self._points, key=lambda s: s.x)

    @property
    def min_point(self):
        assert len(self.points) >= 2, "Count of points <2"
        return self.points[0]

    @property
    def max_point(self):
        assert len(self.points) >= 2, "Count of points <2"
        return self.points[-1]

    @property
    def axis(self) -> AxisMO:
        return self._axis

    @axis.setter
    def axis(self, val: AxisMO):
        self._axis = val


class LightMO(ModelObject):
    def __init__(self, route_type: CELightRouteType, center_point: PointMO, direct_polarity: str,
                 colors: list[CELightColor], stick_type: CELightStickType):
        super().__init__()
        self.route_type = route_type
        self.center_point = center_point
        self.direct_polarity = direct_polarity
        self.colors = colors
        self.stick_type = stick_type


class RailPointMO(ModelObject):
    def __init__(self, center_point: PointMO, plus_point: PointMO, minus_point: PointMO):
        super().__init__()
        self.center_point = center_point
        self.plus_point = plus_point
        self.minus_point = minus_point


class BorderMO(ModelObject):
    def __init__(self, point: PointMO, border_type: CEBorderType):
        super().__init__()
        self.point = point
        self.border_type = border_type


class SectionMO(ModelObject):
    def __init__(self, points: list[PointMO]):
        super().__init__()
        self.points = points
        self.section_type = None
        self.rail_points = []


GLOBAL_CS_SO = CoordinateSystemSOI()
GLOBAL_CS_SO._name = GLOBAL_CS_NAME
GLOBAL_CS_MO = CoordinateSystemMO()
GLOBAL_CS_MO._name = GLOBAL_CS_NAME


# -------------------------        ROUTE CLASSES           -------------------- #


class CrossroadNotification:
    def __init__(self, cn_route: RailRoute, num: int):
        self.route = cn_route
        self.num = num
        self._crsrd_id = None
        self._crsrd_delay_open = None
        self._crsrd_delay_start_notif = None
        self._crsrd_start_notif = None
        self._crsrd_notif_point = None  # not required
        self._crsrd_before_route_points = None  # not required

    @property
    def crsrd_id(self):
        return self._crsrd_id

    @crsrd_id.setter
    def crsrd_id(self, value):
        if (not value) or value.isspace():
            return
        self._crsrd_id = value

    @property
    def crsrd_delay_open(self):
        return self._crsrd_delay_open

    @crsrd_delay_open.setter
    def crsrd_delay_open(self, value):
        if (not value) or value.isspace():
            return
        self.route.int_checker(value, 'crsrd_delay_open_{}'.format(self.num), 0)
        self._crsrd_delay_open = value

    @property
    def crsrd_delay_start_notif(self):
        return self._crsrd_delay_start_notif

    @crsrd_delay_start_notif.setter
    def crsrd_delay_start_notif(self, value):
        if (not value) or value.isspace():
            return
        self.route.int_checker(value, 'crsrd_delay_start_notif_{}'.format(self.num), 0)
        self._crsrd_delay_start_notif = value

    @property
    def crsrd_start_notif(self):
        return self._crsrd_start_notif

    @crsrd_start_notif.setter
    def crsrd_start_notif(self, value):
        if (not value) or value.isspace():
            return
        # ! implement here check start_notif in list of available values
        self._crsrd_start_notif = value

    @property
    def crsrd_notif_point(self):
        return self._crsrd_notif_point

    @crsrd_notif_point.setter
    def crsrd_notif_point(self, value):
        if (not value) or value.isspace():
            return
        self.route.int_checker(value, 'crsrd_notif_point_{}'.format(self.num))
        self._crsrd_notif_point = value

    @property
    def crsrd_before_route_points(self):
        return self._crsrd_before_route_points

    @crsrd_before_route_points.setter
    def crsrd_before_route_points(self, value):
        if (not value) or value.isspace():
            return
        self.route.route_points_checker(value, 'crsrd_before_route_points_{}'.format(self.num))
        self._crsrd_before_route_points = value

    def check_required_params(self):
        if self.route.signal_type == "PpoTrainSignal":
            if self.crsrd_id is None:
                assert (self.crsrd_delay_open is None) and (self.crsrd_delay_start_notif is None) and \
                       (self.crsrd_start_notif is None) and (self.crsrd_notif_point is None) and \
                       (self.crsrd_before_route_points is None), \
                       "Id expected for Crossroad_{} in line {}".format(self.num, self.route.id)
            else:
                assert not (self.crsrd_delay_open is None), "Expected delay_open for Crossroad_{} in line {}".\
                    format(self.num, self.route.id)
                assert not (self.crsrd_delay_start_notif is None), \
                    "Expected delay_start_notif for Crossroad_{} in line {}".format(self.num, self.route.id)
                assert not (self.crsrd_start_notif is None), "Expected start_notif for Crossroad_{} in line {}".\
                    format(self.num, self.route.id)
        elif self.route.signal_type == "PpoShuntingSignal":
            if self.crsrd_id is None:
                assert (self.crsrd_delay_open is None) and (self.crsrd_delay_start_notif is None) and \
                       (self.crsrd_start_notif is None) and (self.crsrd_notif_point is None) and \
                       (self.crsrd_before_route_points is None), \
                       "Id expected for Crossroad_{} in line {}".format(self.num, self.route.id)
            else:
                assert not (self.crsrd_delay_open is None), "Expected delay_open for Crossroad_{} in line {}".\
                    format(self.num, self.route.id)
        else:
            assert False, "Signal type {} not exists".format(self.route.signal_type)


class RailRoute:
    def __init__(self, id_):
        self.id = str(id_)
        self.route_tag = None
        self._route_type = None
        self._signal_tag = None
        self._signal_type = None
        self._route_pointer_value = None
        self._trace_begin = None
        self.trace_points = ""
        self._trace_variants = None
        self._trace_end = None
        self._end_selectors = None
        self._route_points_before_route = None
        self.next_dark = "K"
        self.next_stop = "K"
        self.next_on_main = "K"
        self.next_on_main_green = "K"
        self.next_on_side = "K"
        self.next_also_on_main = "K"
        self.next_also_on_main_green = "K"
        self.next_also_on_side = "K"
        self.crossroad_notifications: list[CrossroadNotification] = []

    def signal_light_checker(self, value, column_name):
        if self.route_type == "PpoShuntingRoute":
            return
        assert value in ["K", "ZH", "Z", "ZHM_Z", "ZHM_ZH", "ZM", "DZH", "DZHM"], \
            "Not supported light value {} in line {} column {}".format(value, self.id, column_name)

    def int_checker(self, value, column_name, min_possible_value: int = 1):
        if value == "":
            return
        assert int(value) >= min_possible_value, "Value should be int >= {}, given value is {} in line {} column {}" \
            .format(min_possible_value, value, self.id, column_name)

    def route_points_checker(self, value, column_name):
        points_found = re.findall(r"[+-]\d{1,3}S?[OB]?", value)
        val_copy = value
        for point in points_found:
            val_copy = val_copy.replace(point, "", 1)
        assert (not val_copy) or val_copy.isspace(), \
            "Pointers list {} is not valid in line {} column {}".format(value, self.id, column_name)

    @property
    def route_type(self):
        return self._route_type

    @route_type.setter
    def route_type(self, value):
        assert value in ["PpoTrainRoute", "PpoShuntingRoute"], "Not valid route type {} in line {}" \
            .format(value, self.id)
        self._route_type = value

    @property
    def signal_tag(self):
        return self._signal_tag

    @signal_tag.setter
    def signal_tag(self, value):
        # ! implement here check signal in list of available values
        self._signal_tag = value

    @property
    def signal_type(self):
        return self._signal_type

    @signal_type.setter
    def signal_type(self, value):
        assert value in ["PpoTrainSignal", "PpoShuntingSignal"], "Not valid signal type {} in line {}" \
            .format(value, self.id)
        self._signal_type = value

    @property
    def route_pointer_value(self):
        return self._route_pointer_value

    @route_pointer_value.setter
    def route_pointer_value(self, value):
        self.int_checker(value, 'route_pointer_value')
        self._route_pointer_value = value

    @property
    def trace_begin(self):
        return self._trace_begin

    @trace_begin.setter
    def trace_begin(self, value):
        # ! implement here check trace_begin in list of available values
        self._trace_begin = value

    @property
    def trace_variants(self):
        return self._trace_variants

    @trace_variants.setter
    def trace_variants(self, value):
        if value == "":
            self._trace_variants = None
            return
        # ! implement here check trace_variants in list of available values
        self._trace_variants = value

    @property
    def trace_points(self):
        return self._trace_points

    @trace_points.setter
    def trace_points(self, value: str):
        self.route_points_checker(value, 'trace_points')
        if value:
            value += " "
        self._trace_points = value

    @property
    def trace_end(self):
        return self._trace_end

    @trace_end.setter
    def trace_end(self, value):
        # ! implement here check trace_end in list of available values
        self._trace_end = value

    @property
    def end_selectors(self):
        return self._end_selectors

    @end_selectors.setter
    def end_selectors(self, value):
        # ! implement here check end_selectors in list of available values
        self._end_selectors = value

    @property
    def route_points_before_route(self):
        return self._route_points_before_route

    @route_points_before_route.setter
    def route_points_before_route(self, value):
        if value == "":
            self._route_points_before_route = None
            return
        # ! implement here check route_points_before_route in list of available values
        self._route_points_before_route = value + " "

    @property
    def next_dark(self):
        return self._next_dark

    @next_dark.setter
    def next_dark(self, value):
        self.signal_light_checker(value, "next_dark")
        self._next_dark = value

    @property
    def next_stop(self):
        return self._next_stop

    @next_stop.setter
    def next_stop(self, value):
        self.signal_light_checker(value, "next_stop")
        self._next_stop = value

    @property
    def next_on_main(self):
        return self._next_on_main

    @next_on_main.setter
    def next_on_main(self, value):
        self.signal_light_checker(value, "next_on_main")
        self._next_on_main = value

    @property
    def next_on_main_green(self):
        return self._next_on_main_green

    @next_on_main_green.setter
    def next_on_main_green(self, value):
        self.signal_light_checker(value, "next_on_main_green")
        self._next_on_main_green = value

    @property
    def next_on_side(self):
        return self._next_on_side

    @next_on_side.setter
    def next_on_side(self, value):
        self.signal_light_checker(value, "next_on_side")
        self._next_on_side = value

    @property
    def next_also_on_main(self):
        return self._next_also_on_main

    @next_also_on_main.setter
    def next_also_on_main(self, value):
        self.signal_light_checker(value, "next_also_on_main")
        self._next_also_on_main = value

    @property
    def next_also_on_main_green(self):
        return self._next_also_on_main_green

    @next_also_on_main_green.setter
    def next_also_on_main_green(self, value):
        self.signal_light_checker(value, "next_also_on_main_green")
        self._next_also_on_main_green = value

    @property
    def next_also_on_side(self):
        return self._next_also_on_side

    @next_also_on_side.setter
    def next_also_on_side(self, value):
        self.signal_light_checker(value, "next_also_on_side")
        self._next_also_on_side = value

    def count_crossroad_notification(self):
        return len(self.crossroad_notifications)

    def add_crossroad_notification(self):
        cn = CrossroadNotification(self, self.count_crossroad_notification() + 1)
        self.crossroad_notifications.append(cn)


def form_route_element(signal_element_, route_: RailRoute) -> ElTr.Element:
    if route_.route_type == "PpoTrainRoute":
        route_element = ElTr.SubElement(signal_element_, 'TrRoute')
    else:
        route_element = ElTr.SubElement(signal_element_, 'ShRoute')
    route_element.set("Tag", route_.route_tag)
    route_element.set("Type", route_.route_type)
    route_element.set("Id", route_.id)
    if route_.route_pointer_value:
        route_element.set("ValueRoutePointer", route_.route_pointer_value)
    trace_element = ElTr.SubElement(route_element, 'Trace')
    trace_element.set("Start", route_.trace_begin)
    trace_element.set("OnCoursePoints", route_.trace_points)
    trace_element.set("Finish", route_.trace_end)
    if route_.trace_variants:
        trace_element.set("Variants", route_.trace_variants)
    selectors_element = ElTr.SubElement(route_element, 'OperatorSelectors')
    selectors_element.set("Ends", route_.end_selectors)
    if route_.route_type == "PpoTrainRoute":
        dependence_element = ElTr.SubElement(route_element, 'SignalingDependence')
        dependence_element.set("Dark", route_.next_dark)
        dependence_element.set("Stop", route_.next_stop)
        dependence_element.set("OnMain", route_.next_on_main)
        dependence_element.set("OnMainGreen", route_.next_on_main_green)
        dependence_element.set("OnSide", route_.next_on_side)
        dependence_element.set("OnMainALSO", route_.next_also_on_main)
        dependence_element.set("OnMainGrALSO", route_.next_also_on_main_green)
        dependence_element.set("OnSideALSO", route_.next_also_on_side)
        if route_.route_points_before_route:
            before_route_element = ElTr.SubElement(route_element, 'PointsAnDTrack')
            before_route_element.set("Points", route_.route_points_before_route)
    for cn_ in route_.crossroad_notifications:
        if cn_.crsrd_id is None:
            continue
        cn_element = ElTr.SubElement(route_element, 'CrossroadNotification')
        cn_element.set("RailCrossing", cn_.crsrd_id)
        cn_element.set("DelayOpenSignal", cn_.crsrd_delay_open)
        if route_.signal_type == "PpoTrainSignal":
            cn_element.set("DelayStartNotification", cn_.crsrd_delay_start_notif)
            cn_element.set("StartNotification", cn_.crsrd_start_notif)
        if not (cn_.crsrd_notif_point is None):
            cn_element.set("NotificationPoint", cn_.crsrd_notif_point)
        if not (cn_.crsrd_before_route_points is None):
            cn_element.set("Point", cn_.crsrd_before_route_points)
    return route_element


# train_routes_dict = OrderedDict()
# shunt_trs_routes_dict = OrderedDict()
# shunt_shs_routes_dict = OrderedDict()
# for route in routes:
#     st = route.signal_tag
#     if route.route_type == "PpoTrainRoute":
#         if st not in train_routes_dict:
#             train_routes_dict[st] = []
#         train_routes_dict[st].append(route)
#     elif route.signal_type == "PpoTrainSignal":
#         if st not in shunt_trs_routes_dict:
#             shunt_trs_routes_dict[st] = []
#         shunt_trs_routes_dict[st].append(route)
#     else:
#         if st not in shunt_shs_routes_dict:
#             shunt_shs_routes_dict[st] = []
#         shunt_shs_routes_dict[st].append(route)

# train_route_element = ElTr.Element('Routes')
# shunt_route_element = ElTr.Element('Routes')
# for train_signal in train_routes_dict:
#     signal_element = ElTr.SubElement(train_route_element, 'TrainSignal')
#     signal_element.set("Tag", train_signal)
#     signal_element.set("Type", "PpoTrainSignal")
#     for route in train_routes_dict[train_signal]:
#         form_route_element(signal_element, route)
#     if train_signal in shunt_trs_routes_dict:
#         for route in shunt_trs_routes_dict[train_signal]:
#             form_route_element(signal_element, route)
# for shunt_signal in shunt_shs_routes_dict:
#     signal_element = ElTr.SubElement(shunt_route_element, 'ShuntingSignal')
#     signal_element.set("Tag", shunt_signal)
#     signal_element.set("Type", "PpoShuntingSignal")
#     for route in shunt_shs_routes_dict[shunt_signal]:
#         form_route_element(signal_element, route)
#
# xmlstr_train = xml.dom.minidom.parseString(ElTr.tostring(train_route_element)).toprettyxml()
# with open('TrainRoute.xml', 'w', encoding='utf-8') as out:
#     out.write(xmlstr_train)
# xmlstr_shunt = xml.dom.minidom.parseString(ElTr.tostring(shunt_route_element)).toprettyxml()
# with open('ShuntingRoute.xml', 'w', encoding='utf-8') as out:
#     out.write(xmlstr_shunt)


# ------------------------------------------------------


def check_expected_type(str_value: str, attr_name: str, image_object: StationObjectImage, names_dict: OrderedDict):
    attr_descr: BaseAttrDescriptor = getattr(image_object.__class__, attr_name)
    if issubclass(attr_descr.expected_type, StationObjectImage):
        if str_value not in names_dict:
            raise ObjectNotFoundCoError("Object {} not found".format(str_value))
        rel_image = names_dict[str_value]
        if not isinstance(rel_image, attr_descr.expected_type):
            raise TypeCoError("Object {} not satisfy required type {}".format(str_value, attr_descr.str_expected_type))
        setattr(image_object, "_{}".format(attr_name), names_dict[str_value])
    else:
        try:
            result = eval(str_value)
        except (ValueError, NameError, SyntaxError):
            raise TypeCoError("Object {} not satisfy required type {}".format(str_value, attr_descr.str_expected_type))
        if not isinstance(result, attr_descr.expected_type):
            raise TypeCoError("Object {} not satisfy required type {}".format(str_value, attr_descr.str_expected_type))
        setattr(image_object, "_{}".format(attr_name), result)


def default_attrib_evaluation(attr_name: str, image: StationObjectImage, names_dict: OrderedDict):
    if attr_name in image.active_attrs:
        setattr(image, "_{}".format(attr_name), None)
        str_attr_value = getattr(image, "_str_{}".format(attr_name))
        if not getattr(image, "_str_{}".format(attr_name)):
            raise RequiredAttributeNotDefinedCOError("Attribute {} required".format(attr_name))
        else:
            check_expected_type(str_attr_value, attr_name, image, names_dict)


class Command:
    def __init__(self, cmd_type: CECommand, cmd_args: list[str]):
        """ Commands have next formats:
        load_config(file_name) (or dir_name)
        create_object(cls_name)
        rename_object(old_name, new_name)
        change_attrib_value(obj_name, attr_name, new_value)
        delete_object(obj_name)
        """
        self.cmd_type = cmd_type
        self.cmd_args = cmd_args


class PicketCoordinate:
    def __init__(self, str_value: str):
        self.str_value = str_value

    @property
    def value(self):
        x = self.str_value
        if x.startswith("PK"):
            try:
                hund_meters = x[x.index("_")+1:x.index("+")]
                meters = x[x.index("+"):]
                hund_meters = int(hund_meters)
                meters = int(meters)
            except ValueError:
                raise PicketCoordinateParsingCoError("Expected int value or picket 'PK_xx+xx'")
            return meters + 100*hund_meters
        else:
            try:
                meters = int(x)
            except ValueError:
                raise PicketCoordinateParsingCoError("Expected int value or picket 'PK_xx+xx'")
            return meters


class CommandSupervisor:
    def __init__(self):
        self.commands = []

    def add_command(self):
        pass

    def remove_command(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass


def execute_commands(commands: list[Command]):
    for command in commands:
        if command.cmd_type == CECommand.load_config:
            dir_name = command.cmd_args[0]
            images = read_station_config(dir_name)
            MODEL.build_dg(images, True)
            MODEL.check_cycle_dg()
            MODEL.rectify_dg()
            MODEL.evaluate_attributes(True)
            MODEL.build_skeleton()
            MODEL.eval_link_length()
            MODEL.build_lights()
            MODEL.build_rail_points()
            MODEL.build_borders()
            MODEL.build_sections()


class ModelProcessor:
    def __init__(self):
        self.names_soi: OrderedDict[str, StationObjectImage] = OrderedDict()
        self.names_mo: OrderedDict[str, OrderedDict[str, ModelObject]] = OrderedDict()  # cls_name: obj_name: obj
        self.rect_so: list[str] = []
        self.refresh_storages()

        self.dg = OneComponentTwoSidedPG()
        gcs_node = self.dg.insert_node()
        gcs_node.append_cell_obj(ImageNameCell(GLOBAL_CS_NAME))

        self.smg = OneComponentTwoSidedPG()

    def refresh_storages(self):
        self.names_soi: OrderedDict[str, StationObjectImage] = OrderedDict({GLOBAL_CS_NAME: GLOBAL_CS_SO})
        self.names_mo: OrderedDict[str, OrderedDict[str, ModelObject]] = OrderedDict()
        self.names_mo["CoordinateSystem"]: OrderedDict[str, CoordinateSystemMO] = OrderedDict()
        self.names_mo["CoordinateSystem"][GLOBAL_CS_NAME] = GLOBAL_CS_MO
        self.rect_so: list[str] = []

    def build_dg(self, images: list[StationObjectImage], from_file: bool = False) -> None:
        if from_file:
            self.refresh_storages()
            for image in images:
                if not image.name:
                    raise NoNameCoError("Name of object in class {} already exist".format(image.__class__.__name__))
                if image.name in self.names_soi:
                    raise ExistingNameCoError("Name {} already exist".format(image.name))
                node = self.dg.insert_node()
                node.append_cell_obj(ImageNameCell(image.name))
                self.names_soi[image.name] = image
            for image in images:
                for attr_name in image.active_attrs:
                    if not getattr(image.__class__, attr_name).enum:
                        attr_value: str = getattr(image, "_str_{}".format(attr_name))
                        for name in self.names_soi:
                            if name.isdigit():  # for rail points
                                continue
                            if " " in attr_value:
                                split_names = attr_value.split(" ")
                            else:
                                split_names = [attr_value]
                            for split_name in split_names:
                                if name == split_name:

                                    node_self: PolarNode = find_cell_name(self.dg.not_inf_nodes,
                                                                          "ImageNameCell", image.name)[1]
                                    node_parent: PolarNode = find_cell_name(self.dg.not_inf_nodes,
                                                                            "ImageNameCell", name)[1]
                                    self.dg.connect_inf_handling(node_self.ni_pu, node_parent.ni_nd)
        else:
            assert False, "build_dg not from file - not implemented"

    def check_cycle_dg(self):
        dg = self.dg
        routes = dg.walk(dg.inf_pu.ni_nd)
        if any([route_.is_cycle for route_ in routes]):
            raise CycleError("Cycle in dependencies was found")

    def rectify_dg(self):
        nodes: list[PolarNode] = list(flatten(self.dg.longest_coverage()))[1:]  # without Global_CS
        self.rect_so = [element_cell_by_type(node, "ImageNameCell").name for node in nodes]

    def evaluate_attributes(self, from_file: bool = False):
        if from_file:
            for image_name in self.rect_so:
                image = self.names_soi[image_name]

                if isinstance(image, CoordinateSystemSOI):
                    default_attrib_evaluation("cs_relative_to", image, self.names_soi)
                    default_attrib_evaluation("x", image, self.names_soi)

                if isinstance(image, AxisSOI):
                    default_attrib_evaluation("cs_relative_to", image, self.names_soi)
                    default_attrib_evaluation("y", image, self.names_soi)
                    default_attrib_evaluation("center_point", image, self.names_soi)
                    default_attrib_evaluation("alpha", image, self.names_soi)

                if isinstance(image, PointSOI):
                    default_attrib_evaluation("axis", image, self.names_soi)
                    default_attrib_evaluation("line", image, self.names_soi)
                    default_attrib_evaluation("cs_relative_to", image, self.names_soi)
                    attr_name = "x"
                    if attr_name in image.active_attrs:
                        setattr(image, "_{}".format(attr_name), None)
                        str_attr_value = getattr(image, "_str_{}".format(attr_name))
                        if not getattr(image, "_str_{}".format(attr_name)):
                            raise RequiredAttributeNotDefinedCOError("Attribute {} required".format(attr_name))
                        else:
                            setattr(image, "_{}".format(attr_name), PicketCoordinate(str_attr_value).value)

                if isinstance(image, LineSOI):
                    attr_name = "points"
                    if attr_name in image.active_attrs:
                        setattr(image, "_{}".format(attr_name), None)
                        str_attr_value: str = getattr(image, "_str_{}".format(attr_name))
                        if not getattr(image, "_str_{}".format(attr_name)):
                            raise RequiredAttributeNotDefinedCOError("Attribute {} required".format(attr_name))
                        else:
                            str_points = str_attr_value.split(" ")
                            if len(str_points) < 2:
                                raise LineDefinitionByPointsCOError("Count of points should be 2, given count <2")
                            if len(str_points) > 2:
                                raise LineDefinitionByPointsCOError("Count of points should be 2, given count >2")
                            str_points: list[str]
                            if str_points[0] == str_points[1]:
                                raise LineDefinitionByPointsCOError("Given points are equal, cannot build line")
                            pnts_list = []
                            for str_value in str_points:
                                if str_value not in self.names_soi:
                                    raise ObjectNotFoundCoError("Object {} not found".format(str_value))
                                rel_image = self.names_soi[str_value]
                                if not isinstance(rel_image, PointSOI):
                                    raise TypeCoError("Object {} not satisfy required type {}"
                                                      .format(str_value, "PointSOI"))
                                pnts_list.append(rel_image)
                            setattr(image, "_{}".format(attr_name), pnts_list)

                if isinstance(image, LightSOI):
                    default_attrib_evaluation("center_point", image, self.names_soi)
                    default_attrib_evaluation("direct_point", image, self.names_soi)
                    attr_name = "colors"
                    if attr_name in image.active_attrs:
                        setattr(image, "_{}".format(attr_name), None)
                        str_attr_value: str = getattr(image, "_str_{}".format(attr_name))
                        if not getattr(image, "_str_{}".format(attr_name)):
                            raise RequiredAttributeNotDefinedCOError("Attribute {} required".format(attr_name))
                        else:
                            str_colors = str_attr_value.split(" ")
                            color_counts = dict(Counter(str_colors))
                            for str_color in color_counts:
                                if str_color not in CELightColor.possible_values:
                                    raise TypeCoError("Color {} for light not possible".format(str_color))
                                if color_counts[str_color] > 1 and str_color != "yellow":
                                    raise TypeCoError("More then 2 lamps for color {} not possible".format(str_color))
                            setattr(image, "_{}".format(attr_name), str_colors)

                if isinstance(image, RailPointSOI):
                    default_attrib_evaluation("center_point", image, self.names_soi)
                    default_attrib_evaluation("dir_plus_point", image, self.names_soi)
                    default_attrib_evaluation("dir_minus_point", image, self.names_soi)

                if isinstance(image, BorderSOI):
                    default_attrib_evaluation("point", image, self.names_soi)

                if isinstance(image, SectionSOI):
                    attr_name = "border_points"
                    if attr_name in image.active_attrs:
                        setattr(image, "_{}".format(attr_name), None)
                        str_attr_value: str = getattr(image, "_str_{}".format(attr_name))
                        if not getattr(image, "_str_{}".format(attr_name)):
                            raise RequiredAttributeNotDefinedCOError("Attribute {} required".format(attr_name))
                        else:
                            str_points = str_attr_value.split(" ")
                            if len(set(str_points)) < len(str_points):
                                raise RepeatingPointsCOError("Points in section border repeating")
                            pnts_list = []
                            for str_value in str_points:
                                if str_value not in self.names_soi:
                                    raise ObjectNotFoundCoError("Object {} not found".format(str_value))
                                rel_image = self.names_soi[str_value]
                                if not isinstance(rel_image, PointSOI):
                                    raise TypeCoError("Object {} not satisfy required type {}"
                                                      .format(str_value, "PointSOI"))
                                pnts_list.append(rel_image)
                            setattr(image, "_{}".format(attr_name), pnts_list)
        else:
            assert False, "evaluate_attributes not from file - not implemented"

    def build_skeleton(self):

        if "CoordinateSystem" not in self.names_mo:
            self.names_mo["CoordinateSystem"] = OrderedDict()
        if "Axis" not in self.names_mo:
            self.names_mo["Axis"] = OrderedDict()
        if "Point" not in self.names_mo:
            self.names_mo["Point"] = OrderedDict()
        if "Line" not in self.names_mo:
            self.names_mo["Line"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, CoordinateSystemSOI):
                model_object = CoordinateSystemMO(self.names_mo["CoordinateSystem"][image.cs_relative_to.name],
                                                  image.x, image.co_x == "true", image.co_y == "true")
                model_object.name = image_name
                self.names_mo["CoordinateSystem"][image_name] = model_object

            if isinstance(image, AxisSOI):
                cs_rel: CoordinateSystemMO = self.names_mo["CoordinateSystem"][image.cs_relative_to.name]
                if image.creation_method == CEAxisCreationMethod.translational:
                    cs_rel_mo: CoordinateSystemMO = self.names_mo["CoordinateSystem"][image.cs_relative_to.name]
                    center_point_x = cs_rel.absolute_x
                    center_point_y = image.y * int(2*(int(cs_rel_mo.absolute_co_y)-0.5))
                    angle = 0
                else:
                    center_point_soi: PointSOI = image.center_point
                    center_point_mo: PointMO = self.names_mo["Point"][center_point_soi]
                    center_point_x = center_point_mo.x
                    center_point_y = center_point_mo.y
                    angle = image.alpha
                    if center_point_soi.on == CEAxisOrLine.line:
                        raise BuildSkeletonError("Building axis by point on line is impossible")
                    if Angle(angle) == Angle(math.pi/2):
                        raise BuildSkeletonError("Building vertical axis is impossible")
                line2D = Line2D(Point2D(center_point_x, center_point_y), angle=Angle(angle))

                model_object = AxisMO(line2D)
                model_object.name = image_name

                for model_object_2 in self.names_mo["Axis"].values():
                    model_object_2: AxisMO
                    try:
                        lines_intersection(model_object.line2D, model_object_2.line2D)
                    except ParallelLinesException:
                        continue
                    except EquivalentLinesException:
                        raise BuildSkeletonError("Cannot re-build existing axis")

                if image.creation_method == CEAxisCreationMethod.rotational:
                    center_point_soi: PointSOI = image.center_point
                    model_object.append_point(center_point_soi)
                self.names_mo["Axis"][image_name] = model_object

            if isinstance(image, PointSOI):
                cs_rel: CoordinateSystemMO = self.names_mo["CoordinateSystem"][image.cs_relative_to.name]
                point_x = cs_rel.absolute_x + image.x * cs_rel.absolute_co_x
                if image.on == CEAxisOrLine.axis:
                    axis: AxisMO = self.names_mo["Axis"][image.axis.name]
                    pnt2D = lines_intersection(axis.line2D, Line2D(Point2D(point_x, 0), angle=Angle(math.pi / 2)))
                else:
                    line: LineMO = self.names_mo["Line"][image.line.name]
                    try:
                        pnt2D_y = line.boundedCurves[0].y_by_x(point_x)
                    except OutBorderException:
                        if len(line.boundedCurves) == 1:
                            raise BuildSkeletonError("Point out of borders")
                        else:
                            try:
                                pnt2D_y = line.boundedCurves[1].y_by_x(point_x)
                            except OutBorderException:
                                raise BuildSkeletonError("Point out of borders")
                    pnt2D = Point2D(point_x, pnt2D_y)

                model_object = PointMO(pnt2D)
                model_object.name = image_name

                for model_object_2 in self.names_mo["Point"].values():
                    model_object_2: PointMO
                    try:
                        evaluate_vector(model_object.point2D, model_object_2.point2D)
                    except PointsEqualException:
                        raise BuildSkeletonError("Cannot re-build existing point")

                if image.on == CEAxisOrLine.axis:
                    axis: AxisMO = self.names_mo["Axis"][image.axis.name]
                    self.point_to_axis_handling(model_object, axis)
                else:
                    line: LineMO = self.names_mo["Line"][image.line.name]
                    self.point_to_line_handling(model_object, line)
                self.names_mo["Point"][image_name] = model_object

            if isinstance(image, LineSOI):
                points_so: list[PointSOI] = image.points
                points_mo: list[PointMO] = [self.names_mo["Point"][point.name] for point in points_so]
                point_1, point_2 = points_mo[0], points_mo[1]
                axises_mo: list[AxisMO] = []
                for point_so in points_so:
                    if point_so.on == CEAxisOrLine.line:
                        line_mo: LineMO = self.names_mo["Line"][point_so.line.name]
                        if not line_mo.axis:
                            raise BuildSkeletonError("Cannot build line by point on line")
                        axises_mo.append(line_mo.axis)
                    else:
                        axis_mo: AxisMO = self.names_mo["Axis"][point_so.axis.name]
                        axises_mo.append(axis_mo)
                axis_1, axis_2 = axises_mo[0], axises_mo[1]
                if axis_1 is axis_2:
                    boundedCurves = [BoundedCurve(point_1.point2D, point_2.point2D)]
                elif axis_1.angle == axis_2.angle:
                    center_point = Point2D(0.5*(point_1.point2D.x+point_2.point2D.x),
                                           0.5*(point_1.point2D.y+point_2.point2D.y))
                    boundedCurves = [BoundedCurve(point_1.point2D, center_point, axis_1.angle),
                                     BoundedCurve(point_2.point2D, center_point, axis_2.angle)]
                else:
                    boundedCurves = [BoundedCurve(point_1.point2D, point_2.point2D, axis_1.angle, axis_2.angle)]
                model_object = LineMO(boundedCurves)
                model_object.name = image_name

                model_object.append_point(point_1)
                model_object.append_point(point_2)
                if axis_1 is axis_2:
                    self.line_to_axis_handling(model_object, axis_1)
                else:
                    self.line_connection_handling(point_1, point_2)
                self.names_mo["Line"][image_name] = model_object

    def point_to_line_handling(self, point: PointMO, line: LineMO):
        old_points = line.points
        prev_point, next_point = None, None
        place_found = False
        for i_ in range(len(old_points)-1):
            if old_points[i_].x < point.x < old_points[i_+1].x:
                place_found = True
                prev_point, next_point = old_points[i_], old_points[i_+1]
        assert place_found, "point before inserting not found"
        assert next_point, "end of point list"

        prev_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, "PointCell", prev_point.name)[1]
        next_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, "PointCell", next_point.name)[1]

        new_point_node = self.smg.insert_node(next_node.ni_nd, prev_node.ni_pu)
        new_point_node.append_cell_obj(PointCell(point.name))

        line.append_point(point)

    def point_to_axis_handling(self, point: PointMO, axis: AxisMO):
        lines = axis.lines
        for line in lines:
            if line.min_point.x < point.x < line.max_point.x:
                self.point_to_line_handling(point, line)
                break

        axis.append_point(point)

    def line_connection_handling(self, pnt_1: PointMO, pnt_2: PointMO):
        min_point, max_point = (pnt_1, pnt_2) if (pnt_1.x < pnt_2.x) else (pnt_2, pnt_1)

        try:

            min_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, "PointCell", min_point.name)[1]
        except NotFoundCellError:
            min_node = self.smg.insert_node()
            min_node.append_cell_obj(PointCell(min_point.name))

        try:
            max_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, "PointCell", max_point.name)[1]
        except NotFoundCellError:
            max_node = self.smg.insert_node()
            max_node.append_cell_obj(PointCell(max_point.name))

        self.smg.connect_inf_handling(min_node.ni_pu, max_node.ni_nd)

    def line_to_axis_handling(self, line: LineMO, axis: AxisMO):
        old_lines = axis.lines
        axis_points = axis.points
        for old_line in old_lines:
            if (line.min_point.x > old_line.max_point.x) or (old_line.min_point.x > line.max_point.x):
                continue
            else:
                raise BuildSkeletonError("lines intersection on axis found")
        on_line_points = axis_points[axis_points.index(line.min_point):axis_points.index(line.max_point)+1]
        last_nd_interface = self.smg.inf_pu.ni_nd
        for line_point in reversed(on_line_points):
            try:
                point_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, "PointCell", line_point.name)[1]
                self.smg.connect_inf_handling(last_nd_interface, point_node.ni_pu)
            except NotFoundCellError:
                point_node = self.smg.insert_node(last_nd_interface)
                point_node.append_cell_obj(PointCell(line_point.name))
            last_nd_interface = point_node.ni_nd

        axis.append_line(line)
        line.axis = axis

    def eval_link_length(self):
        for link in self.smg.not_inf_links:
            pn_s_ = [ni.pn for ni in link.ni_s]
            pnt_cells_: list[PointCell] = [element_cell_by_type(pn, "PointCell") for pn in pn_s_]
            link.append_cell_obj(LengthCell(abs(self.names_mo["Point"][pnt_cells_[0].name].x -
                                                self.names_mo["Point"][pnt_cells_[1].name].x)))

    def build_lights(self):

        if "Light" not in self.names_mo:
            self.names_mo["Light"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, LightSOI):
                center_point: PointMO = self.names_mo["Point"][image.center_point.name]
                direct_point: PointMO = self.names_mo["Point"][image.direct_point.name]

                if center_point is direct_point:
                    raise BuildEquipmentError("Direction point is equal to central point")

                # check direction
                center_point_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, "PointCell", center_point.name)[1]
                direct_point_node = find_cell_name(self.smg.not_inf_nodes, "PointCell", direct_point.name)[1]
                routes_node_to_node = self.smg.routes_node_to_node(center_point_node, direct_point_node)
                if not routes_node_to_node:
                    raise BuildEquipmentError("Route from central point to direction point not found")
                ni = routes_node_to_node[1]
                if ni.end == 'nd':
                    direction_ni = 'nd'
                else:
                    direction_ni = 'pu'

                model_object = LightMO(image.light_route_type, center_point, direction_ni,
                                       image.colors, image.light_stick_type)
                center_point_node.append_cell_obj(LightCell(model_object.name))

                model_object.name = image_name
                self.names_mo["Light"][image_name] = model_object

    def build_rail_points(self):

        if "RailPoint" not in self.names_mo:
            self.names_mo["RailPoint"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, RailPointSOI):
                center_point: PointMO = self.names_mo["Point"][image.center_point.name]
                plus_point: PointMO = self.names_mo["Point"][image.dir_plus_point.name]
                minus_point: PointMO = self.names_mo["Point"][image.dir_minus_point.name]

                # check direction
                center_point_node = find_cell_name(self.smg.not_inf_nodes, "PointCell", center_point.name)[1]
                plus_point_node = find_cell_name(self.smg.not_inf_nodes, "PointCell", plus_point.name)[1]
                minus_point_node = find_cell_name(self.smg.not_inf_nodes, "PointCell", minus_point.name)[1]
                plus_routes, ni_plus = self.smg.routes_node_to_node(center_point_node, plus_point_node)
                minus_routes, ni_minus = self.smg.routes_node_to_node(center_point_node, minus_point_node)
                if not plus_routes:
                    raise BuildEquipmentError("Route from central point to '+' point not found")
                if not minus_routes:
                    raise BuildEquipmentError("Route from central point to '-' point not found")
                for plus_route in plus_routes:
                    for minus_route in minus_routes:
                        if plus_route.partially_overlaps(minus_route):
                            raise BuildEquipmentError("Cannot understand '+' and '-' directions because their overlaps")
                if not (ni_plus is ni_minus):
                    raise BuildEquipmentError("Defined '+' or '-' direction is equal to 0-direction")

                # + and - move cells
                plus_route = plus_routes[0]
                plus_link = plus_route.links[0]
                plus_move = ni_plus.get_move_by_link(plus_link)
                plus_move.append_cell_obj(RailPointDirectionCell("+{}".format(image.name)))
                minus_route = minus_routes[0]
                minus_link = minus_route.links[0]
                minus_move = ni_minus.get_move_by_link(minus_link)
                minus_move.append_cell_obj(RailPointDirectionCell("-{}".format(image.name)))

                model_object = RailPointMO(center_point, plus_point, minus_point)
                model_object.name = image_name
                self.names_mo["RailPoint"][image_name] = model_object

    def build_borders(self):

        if "Border" not in self.names_mo:
            self.names_mo["Border"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, BorderSOI):
                point: PointMO = self.names_mo["Point"][image.point.name]

                model_object = BorderMO(point, image.border_type)
                model_object.name = image_name
                self.names_mo["Border"][image_name] = model_object

    def build_sections(self):

        if "Section" not in self.names_mo:
            self.names_mo["Section"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, SectionSOI):
                border_points: list[PointMO] = [self.names_mo["Point"][point.name] for point in image.border_points]
                point_nodes: list[PolarNode] = [find_cell_name(self.smg.not_inf_nodes, "PointCell", point.name)[1]
                                                for point in border_points]
                closed_links = self.smg.closed_links(point_nodes)
                if not closed_links:
                    raise BuildEquipmentError("No closed links found")

                # links sections
                for link in closed_links:
                    try:
                        element_cell_by_type(link, "IsolatedSectionCell")
                    except NotFoundCellError:
                        pass
                    else:
                        raise BuildEquipmentError("Section in link already exists")
                    link.append_cell_obj(IsolatedSectionCell(image.name))

                model_object = SectionMO(border_points)
                model_object.name = image_name
                self.names_mo["Section"][image_name] = model_object

    def eval_routes(self, train_routes_file_name, shunting_routes_file_name):
        routes = []

        # 1. Form routes from smg
        light_cells_ = all_cells_of_type(self.smg.not_inf_nodes, "LightCell")


MODEL = ModelProcessor()


if __name__ == "__main__":
    test_1 = False
    if test_1:
        cs = CoordinateSystemSOI()
        print(cs.attr_sequence_template)
        print(cs.dependence)
        print(cs.active_attrs)
        cs.dependence = "independent"
        print()
        print(cs.active_attrs)
        cs.dependence = "dependent"
        print()
        print(cs.active_attrs)
        print(SOIS.class_objects)
        print(getattr(CsDepend, "__set__") == BaseAttrDescriptor.__set__)
        print(getattr(RailPDirMinusPoint, "__set__") == BaseAttrDescriptor.__set__)
        cs.cs_relative_to = "GlobalCS"
        cs.x = "35"
        cs.co_x = "false"

        for attr in cs.active_attrs:
            print(getattr(cs, attr))

        print(cs.dict_possible_values)
        print(cs.dict_values)

    test_2 = False
    if test_2:
        pnt = PointSOI()
        pnt.name = "Point"
        pnt.on = "line"
        SOIS.add_new_object(pnt)
        for attr in pnt.active_attrs:
            print(getattr(pnt, attr))
        ax = AxisSOI()
        ax.creation_method = "rotational"
        print()
        ax.center_point = "Point"
        for attr in ax.active_attrs:
            print(getattr(ax, attr))

    test_3 = False
    if test_3:
        pnt = PointSOI()
        pnt.x = "PK_12+34"
        print(type(pnt.x))
        print(pnt.x)
        print(PointSOI.attr_sequence_template)

    test_4 = False
    if test_4:
        cs = CoordinateSystemSOI()
        print(CoordinateSystemSOI.dict_possible_values)
        print(cs.dict_possible_values)

    test_5 = False
    if test_5:
        make_xlsx_templates(STATION_OUT_CONFIG_FOLDER)

    test_6 = False
    if test_6:
        objs = read_station_config(STATION_IN_CONFIG_FOLDER)
        # pnt = get_object_by_name("Point_15", objs)
        print(pnt.dict_possible_values)
        print(pnt.__class__.dict_possible_values)
        # for attr_ in pnt.active_attrs:
        #     print(getattr(pnt, attr_))

    test_7 = False
    if test_7:
        pnt = PointSOI()
        pnt.x = "PK_12+34"
        print(pnt.x)

    test_8 = False
    if test_8:
        objs = read_station_config(STATION_IN_CONFIG_FOLDER)
        # SOIR.build_dg(objs)
        # SOIR.check_cycle()
        # print([obj.name for obj in SOIR.rectified_object_list()])
        # build_model(SOIR.rectified_object_list())

    test_9 = False
    if test_9:
        execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
        print(MODEL.names_soi)
        print(MODEL.names_mo)

        # cs_1: CoordinateSystemMO = MODEL.names_mo['CS_1']
        # print(cs_1.absolute_x)
        # print(cs_1.absolute_y)
        # print(cs_1.absolute_co_x)
        # print(cs_1.absolute_co_y)
        # if 'CS_2' in MODEL.names_mo:
        #     cs_2 = MODEL.names_mo['CS_2']
        #     print(cs_2.absolute_x)
        #     print(cs_2.absolute_y)
        #     print(cs_2.absolute_co_x)
        #     print(cs_2.absolute_co_y)
        # if 'CS_3' in MODEL.names_mo:
        #     cs_3 = MODEL.names_mo['CS_3']
        #     print(cs_3.absolute_x)
        #     print(cs_3.absolute_y)
        #     print(cs_3.absolute_co_x)
        #     print(cs_3.absolute_co_y)

        ax_1: AxisMO = MODEL.names_mo['Axis_1']
        print(ax_1.line2D)

        line_2: LineMO = MODEL.names_mo['Line_7']
        print(line_2.boundedCurves)

        # pnt_15: PointMO = MODEL.names_mo['Axis_1']
        # print(ax_1.line2D)

    test_10 = True
    if test_10:

        execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
        print(MODEL.names_soi)
        # print(MODEL.names_soi.keys())  # .rect_so
        print(MODEL.rect_so)
        print(MODEL.names_mo)

        # line_1_node = get_point_node_DG("Line_1")
        # line_6_node = get_point_node_DG("Line_6")
        # point_16_node = get_point_node_DG("Point_16")
        # print("line_1_node", line_1_node)
        # print("line_6_node", line_6_node)
        # print("line_6 up connections", [link.opposite_ni(line_6_node.ni_pu).pn for link in line_6_node.ni_pu.links])
        # print("point_16_node", point_16_node)
        # print("point_16 up connections", [link.opposite_ni(point_16_node.ni_pu).pn for link in point_16_node.ni_pu.links])
        #
        # print(MODEL.dg.longest_coverage())
        # print("len routes", len(MODEL.dg.walk(MODEL.dg.inf_pu.ni_nd)))
        # i=0
        # for route in MODEL.dg.walk(MODEL.dg.inf_pu.ni_nd):
        #     if (line_6_node in route.nodes) or (line_6_node in route.nodes):
        #         i+=1
        #         print("i=", i)
        #         print("nodes", route.nodes)

        # ax_1: AxisMO = MODEL.names_mo['Axis_2']
        # print([pnt.x for pnt in ax_1.points])
        print(len(MODEL.smg.not_inf_nodes))

        print("minus inf", MODEL.smg.inf_nd)
        print("plus inf", MODEL.smg.inf_pu)
        for i in range(20):
            try:
                pnt_name = "Point_{}".format(str(i+1))
                pnt_node: PolarNode = find_cell_name(MODEL.smg.not_inf_nodes, "PointCell", pnt_name)[1]
                print(pnt_name+" =>", pnt_node)
                print("nd-connections", [link.opposite_ni(pnt_node.ni_nd).pn for link in pnt_node.ni_nd.links])
                print("pu-connections", [link.opposite_ni(pnt_node.ni_pu).pn for link in pnt_node.ni_pu.links])
            except NotFoundCellError:
                continue
        print("len of links", len(MODEL.smg.links))
        for link in MODEL.smg.not_inf_links:
            print()
            ni_s = link.ni_s
            pn_s = [ni.pn for ni in link.ni_s]
            pnt_cells: list[PointCell] = [element_cell_by_type(pn, "PointCell") for pn in pn_s]
            print("link between {}, {}".format(pnt_cells[0].name, pnt_cells[1].name))
            print("length {}".format(element_cell_by_type(link, "LengthCell").length))
            for ni in ni_s:
                move = ni.get_move_by_link(link)
                if move.cell_objs:
                    rpdc = element_cell_by_type(move, "RailPointDirectionCell")
                    print("Rail point direction = ", rpdc.direction)
            print("section {}".format(element_cell_by_type(link, "IsolatedSectionCell").name))

    test_11 = False
    if test_11:
        execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
        light_cells = all_cells_of_type(MODEL.smg.not_inf_nodes, "LightCell")
        print(len(light_cells))

    test_12 = False
    if test_12:
        execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
        MODEL.eval_routes("TrainRoute.xml", "ShuntingRoute.xml")
