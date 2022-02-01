from __future__ import annotations
from typing import Type, Union
from collections import OrderedDict
from copy import copy

from custom_enum import CustomEnum
from enums_images import CEDependence, CEBool, CEAxisCreationMethod, CEAxisOrLine, CELightRouteType, CELightStickType, \
    CEBorderType


class SOIAttrSeqTemplate:
    def __get__(self, instance, owner) -> list[str]:

        if owner == CoordinateSystemSOI:
            return ["cs_relative_to",
                    "dependence",
                    "x",
                    "co_x",
                    "co_y"]

        if owner == AxisSOI:
            return ["cs_relative_to",
                    "creation_method",
                    "y",
                    "center_point",
                    "alpha"]

        if owner == PointSOI:
            return ["on",
                    "axis",
                    "line",
                    "cs_relative_to",
                    "x"]

        if owner == LineSOI:
            return ["points"]

        if owner == LightSOI:
            return ["light_route_type",
                    "center_point",
                    "direct_point",
                    "colors",
                    "light_stick_type"]

        if owner == RailPointSOI:
            return ["center_point",
                    "dir_plus_point",
                    "dir_minus_point"]

        if owner == BorderSOI:
            return ["point",
                    "border_type"]

        if owner == SectionSOI:
            return ["border_points"]

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
        """ returns Odict[str, list[str]] """
        if instance is None:
            """ for owner - all enum attributes """
            result = OrderedDict()
            for attr_ in owner.attr_sequence_template:
                attrib = getattr(owner, attr_)
                if attrib.enum:
                    result[attr_] = attrib.enum.possible_values
                else:
                    result[attr_] = []
        else:
            """ instance - only for active """
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
                self.str_expected_type: str = expected_type
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


if __name__ == "__main__":
    cs = CoordinateSystemSOI()
    cs.cs_relative_to = "Global"
    print(cs._str_cs_relative_to)
    cs_2 = copy(cs)
    cs.cs_relative_to = "NonGlobal"
    print(cs._str_cs_relative_to)
    print(cs_2._str_cs_relative_to)
    print(cs, cs_2)
