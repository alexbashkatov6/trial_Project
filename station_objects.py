from __future__ import annotations
from typing import Union

from enums_images import CEDependence, CEBool, CEAxisCreationMethod, CEAxisOrLine, CELightRouteType, CELightStickType, \
    CELightColor, CEBorderType


class SoAttrSeq:
    def __get__(self, instance, owner):
        if owner == CoordinateSystem:
            return [CoordinateSystem.cs_relative_to,
                    {CoordinateSystem.dependence: CEDependence.possible_values},
                    [[CoordinateSystem.x, CoordinateSystem.y],
                     [CoordinateSystem.alpha]],
                    {CoordinateSystem.co_x: CEBool.possible_values},
                    {CoordinateSystem.co_y: CEBool.possible_values}]
        if owner == Axis:
            return [Axis.cs_relative_to,
                    {Axis.creation_method: CEAxisCreationMethod.possible_values},
                    [[Axis.y],
                     [Axis.center_point, Axis.alpha]]]
        if owner == Point:
            return [{Point.on: CEAxisOrLine.possible_values},
                    Point.x]
        if owner == Line:
            return [Line.points]
        if owner == Light:
            return [{Light.light_route_type: CELightRouteType.possible_values},
                    {Light.light_stick_type: CELightStickType.possible_values},
                    Light.colors]
        if owner == RailPoint:
            return [RailPoint.center_point,
                    RailPoint.dir_plus_point,
                    RailPoint.dir_minus_point]
        if owner == Border:
            return [{Border.border_type: CEBorderType.possible_values}]
        if owner == Section:
            return [Section.border_points]

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class SoActiveAttrs:
    pass


class SoName:
    pass


class BaseAttrDescriptor:

    def __get__(self, instance, owner):
        if not instance:
            return self.name
        else:
            return getattr(instance, "_"+self.name)

    def __set_name__(self, owner, name):
        self.name = name


class CsCsRelTo(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class CsDepend(BaseAttrDescriptor):

    def __set__(self, instance, value):
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

    def __set__(self, instance, value):
        pass


class CsCoY(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class AxCsRelTo(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class AxCrtMethod(BaseAttrDescriptor):

    def __set__(self, instance, value):
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

    def __set__(self, instance, value):
        pass


class PntX(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class LinePoints(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class LightRouteType(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class LightStickType(BaseAttrDescriptor):

    def __set__(self, instance, value):
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

    def __set__(self, instance, value):
        pass


class SectBorderPoints(BaseAttrDescriptor):

    def __set__(self, instance, value):
        pass


class StationObject:
    attr_sequence = SoAttrSeq()
    active_attrs = SoActiveAttrs()
    name = SoName()

    def switch_branch(self):
        pass


class CoordinateSystem(StationObject):
    cs_relative_to = CsCsRelTo()
    dependence = CsDepend()
    x = CsX()
    y = CsY()
    alpha = CsAlpha()
    co_x = CsCoX()
    co_y = CsCoY()


class Axis(StationObject):
    cs_relative_to = AxCsRelTo()
    creation_method = AxCrtMethod()
    y = AxY()
    center_point = AxCenterPoint()
    alpha = AxAlpha()


class Point(StationObject):
    on = PntOn()
    x = PntX()


class Line(StationObject):
    points = LinePoints()


class Light(StationObject):
    light_route_type = LightRouteType()
    light_stick_type = LightStickType()
    center_point = LightCenterPoint()
    direct_point = LightDirectionPoint()
    colors = LightColors()


class RailPoint(StationObject):
    center_point = RailPCenterPoint()
    dir_plus_point = RailPDirPlusPoint()
    dir_minus_point = RailPDirMinusPoint()


class Border(StationObject):
    border_type = BorderType()


class Section(StationObject):
    border_points = SectBorderPoints()


class StationObjectsStorage:
    pass


if __name__ == "__main__":
    cs = CoordinateSystem()
    print(cs.attr_sequence)
