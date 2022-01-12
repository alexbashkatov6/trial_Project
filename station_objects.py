from __future__ import annotations
from typing import Type

from custom_enum import CustomEnum


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


class SoAttrSeqTemplate:
    def __get__(self, instance, owner) -> list[str]:

        if owner == CoordinateSystem:
            return [CoordinateSystem.cs_relative_to,
                    CoordinateSystem.dependence,
                    CoordinateSystem.x,
                    CoordinateSystem.y,
                    CoordinateSystem.alpha,
                    CoordinateSystem.co_x,
                    CoordinateSystem.co_y]

        if owner == Axis:
            return [Axis.cs_relative_to,
                    Axis.creation_method,
                    Axis.y,
                    Axis.center_point,
                    Axis.alpha]

        if owner == Point:
            return [Point.on,
                    Point.x]

        if owner == Line:
            return [Line.points]

        if owner == Light:
            return [Light.light_route_type,
                    Light.light_stick_type,
                    Light.colors]

        if owner == RailPoint:
            return [RailPoint.center_point,
                    RailPoint.dir_plus_point,
                    RailPoint.dir_minus_point]

        if owner == Border:
            return [Border.border_type]

        if owner == Section:
            return [Section.border_points]

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class SoActiveAttrs:
    def __get__(self, instance, owner):
        assert instance, "Only for instance"
        instance: StationObject
        instance._active_attrs = instance.attr_sequence_template

        if owner == CoordinateSystem:
            instance: CoordinateSystem
            if instance.dependence == CEDependence.dependent:
                instance._active_attrs.remove(CoordinateSystem.alpha)
            else:
                instance._active_attrs.remove(CoordinateSystem.x)
                instance._active_attrs.remove(CoordinateSystem.y)

        if owner == Axis:
            instance: Axis
            if instance.creation_method == CEAxisCreationMethod.rotational:
                instance._active_attrs.remove(Axis.y)
            else:
                instance._active_attrs.remove(Axis.alpha)
                instance._active_attrs.remove(Axis.center_point)

        return instance._active_attrs

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class SoListPossibleValues:
    pass


class SoListValues:
    pass


class SoName:
    def __get__(self, instance, owner):
        assert instance, "Only for instance"
        return instance._name

    def __set__(self, instance, value: str):
        if value in SOS.name_to_object:
            raise ExistingNameCoError("Name {} already exists".format(value))
        instance._name = value


class BaseAttrDescriptor:

    def __init__(self, expected_type_or_enum=None):
        self.enum = None
        self.expected_type = None
        if expected_type_or_enum:
            if isinstance(expected_type_or_enum, CustomEnum):
                self.enum = expected_type_or_enum
            else:
                assert issubclass(expected_type_or_enum, StationObject) or \
                       (expected_type_or_enum in [str, int, float]), "StationObject type or str, int, float expected"
                self.expected_type: Type = expected_type_or_enum

    def __get__(self, instance, owner):
        if not instance:
            return self.name
        elif hasattr(instance, "_"+self.name):
            return getattr(instance, "_"+self.name)
        elif self.enum:
            setattr(instance, "_"+self.name, self.enum)
            return getattr(instance, "_"+self.name)
        else:
            return None

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value: str):
        """ ! implement pre-set - before semantic check """
        if self.enum:
            inst_enum: CustomEnum = getattr(instance, self.name)
            setattr(instance, "_" + self.name, type(inst_enum)(value))
        elif self.expected_type:
            if issubclass(self.expected_type, StationObject):
                if value in SOS.name_to_object:
                    setattr(instance, "_" + self.name, SOS.name_to_object[value])
            else:
                setattr(instance, "_" + self.name, self.expected_type(value))


class CsCsRelTo(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class CsDepend(BaseAttrDescriptor):
    pass


class CsX(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class CsY(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class CsAlpha(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class CsCoX(BaseAttrDescriptor):
    pass


class CsCoY(BaseAttrDescriptor):
    pass


class AxCsRelTo(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class AxCrtMethod(BaseAttrDescriptor):
    pass


class AxY(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class AxCenterPoint(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class AxAlpha(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class PntOn(BaseAttrDescriptor):
    pass


class PntX(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class LinePoints(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class LightRouteType(BaseAttrDescriptor):
    pass


class LightStickType(BaseAttrDescriptor):
    pass


class LightCenterPoint(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class LightDirectionPoint(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class LightColors(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class RailPCenterPoint(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class RailPDirPlusPoint(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class RailPDirMinusPoint(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class BorderType(BaseAttrDescriptor):
    pass


class SectBorderPoints(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class StationObject:
    attr_sequence_template = SoAttrSeqTemplate()
    active_attrs = SoActiveAttrs()
    list_possible_values = SoListPossibleValues()
    list_values = SoListValues()
    name = SoName()


class CoordinateSystem(StationObject):
    cs_relative_to = CsCsRelTo()
    dependence = CsDepend(CEDependence(CEDependence.dependent))
    x = CsX()
    y = CsY()
    alpha = CsAlpha()
    co_x = CsCoX(CEBool(CEBool.true))
    co_y = CsCoY(CEBool(CEBool.true))


class Axis(StationObject):
    cs_relative_to = AxCsRelTo()
    creation_method = AxCrtMethod(CEAxisCreationMethod(CEAxisCreationMethod.translational))
    y = AxY()
    center_point = AxCenterPoint()
    alpha = AxAlpha()


class Point(StationObject):
    on = PntOn(CEAxisOrLine(CEAxisOrLine.axis))
    x = PntX()


class Line(StationObject):
    points = LinePoints()


class Light(StationObject):
    light_route_type = LightRouteType(CELightRouteType(CELightRouteType.train))
    light_stick_type = LightStickType(CELightStickType(CELightStickType.mast))
    center_point = LightCenterPoint()
    direct_point = LightDirectionPoint()
    colors = LightColors()


class RailPoint(StationObject):
    center_point = RailPCenterPoint()
    dir_plus_point = RailPDirPlusPoint()
    dir_minus_point = RailPDirMinusPoint()


class Border(StationObject):
    border_type = BorderType(CEBorderType(CEBorderType.standoff))


class Section(StationObject):
    border_points = SectBorderPoints()


class StationObjectsStorage:
    def __init__(self):
        self.name_to_object: dict[str, StationObject] = {}
        self.class_objects = dict.fromkeys([cls.__name__ for cls in StationObject.__subclasses__()], [])

    def add_new_object(self, obj: StationObject):
        self.class_objects[obj.__class__.__name__].append(obj.name)
        self.name_to_object[obj.name] = obj


SOS = StationObjectsStorage()

if __name__ == "__main__":
    cs = CoordinateSystem()
    print(cs.attr_sequence_template)
    print(cs.dependence)
    print(cs.active_attrs)
    cs.dependence = "independent"
    print()
    print(cs.active_attrs)
    cs.dependence = "dependent"
    print()
    print(cs.active_attrs)
    print(SOS.class_objects)
