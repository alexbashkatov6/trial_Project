from __future__ import annotations
from collections import OrderedDict
from copy import copy

from custom_enum import CustomEnum


class NotImplementedCoError(Exception):
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
        instance: StationObjectImage
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
        return getattr(instance, "_name")

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
                self.expected_type: str = expected_type_or_enum

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

    def __set__(self, instance: StationObjectImage, value: str):
        assert self.name in instance.active_attrs, "Attribute for set should be active"
        if self.enum:
            inst_enum: CustomEnum = getattr(instance, self.name)
            setattr(instance, "_" + self.name, type(inst_enum)(value))
        elif self.expected_type:
            if self.expected_type == "complex_type":
                return
            else:
                """ because class cannot contain its name, eval needs """
                expected_type = eval(self.expected_type)

            if issubclass(expected_type, StationObjectImage):
                if value in SOS.name_to_object:
                    obj = SOS.name_to_object[value]
                    if isinstance(obj, expected_type):
                        setattr(instance, "_pre_" + self.name, obj)
                    else:
                        raise TypeCoError("Type of given object {} not satisfy type requirement {}"
                                          .format(value, expected_type))
                else:
                    raise TypeCoError("Type of given object {} not satisfy type requirement {}"
                                      .format(value, expected_type))
            elif expected_type in [str, int, float]:
                try:
                    val = expected_type(value)
                except ValueError:
                    raise TypeCoError("Type of given object {} not satisfy type requirement {}"
                                      .format(value, expected_type))
                setattr(instance, "_pre_" + self.name, val)
            else:
                assert False, "StationObject type or str, int, float expected"

            if self.__class__.__set__ is BaseAttrDescriptor.__set__:
                self.push_pre_to_value(instance)
        else:
            assert False, "No requirements found"

    def get_pre_value(self, instance: StationObjectImage):
        return getattr(instance, "_pre_" + self.name)

    def push_pre_to_value(self, instance: StationObjectImage):
        setattr(instance, "_" + self.name, getattr(instance, "_pre_" + self.name))


class CsCsRelTo(BaseAttrDescriptor):
    pass


class CsDepend(BaseAttrDescriptor):
    pass


class CsX(BaseAttrDescriptor):
    pass


class CsY(BaseAttrDescriptor):
    pass


class CsAlpha(BaseAttrDescriptor):
    def __set__(self, instance, value):
        raise NotImplementedCoError


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

    def __set__(self, instance, value):
        super().__set__(instance, value)
        point: Point = self.get_pre_value(instance)
        if point.on != "axis":
            raise SemanticCoError("Center point should be on Axis")
        else:
            self.push_pre_to_value(instance)


class AxAlpha(BaseAttrDescriptor):
    pass


class PntOn(BaseAttrDescriptor):
    pass


class PntX(BaseAttrDescriptor):
    pass


class LinePoints(BaseAttrDescriptor):

    def __set__(self, instance, value: tuple[str, str]):
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


class StationObjectImage:
    attr_sequence_template = SoAttrSeqTemplate()
    active_attrs = SoActiveAttrs()
    list_possible_values = SoListPossibleValues()
    list_values = SoListValues()
    name = SoName()


class CoordinateSystem(StationObjectImage):
    cs_relative_to = CsCsRelTo("CoordinateSystem")
    dependence = CsDepend(CEDependence(CEDependence.dependent))
    x = CsX("int")
    y = CsY("int")
    alpha = CsAlpha("int")
    co_x = CsCoX(CEBool(CEBool.true))
    co_y = CsCoY(CEBool(CEBool.true))


class Axis(StationObjectImage):
    cs_relative_to = AxCsRelTo("CoordinateSystem")
    creation_method = AxCrtMethod(CEAxisCreationMethod(CEAxisCreationMethod.translational))
    y = AxY("int")
    center_point = AxCenterPoint("Point")
    alpha = AxAlpha("int")


class Point(StationObjectImage):
    on = PntOn(CEAxisOrLine(CEAxisOrLine.axis))
    x = PntX("int")


class Line(StationObjectImage):
    points = LinePoints("complex_type")


class Light(StationObjectImage):
    light_route_type = LightRouteType(CELightRouteType(CELightRouteType.train))
    light_stick_type = LightStickType(CELightStickType(CELightStickType.mast))
    center_point = LightCenterPoint("Point")
    direct_point = LightDirectionPoint("Point")
    colors = LightColors("complex_type")


class RailPoint(StationObjectImage):
    center_point = RailPCenterPoint("Point")
    dir_plus_point = RailPDirPlusPoint("Point")
    dir_minus_point = RailPDirMinusPoint("Point")


class Border(StationObjectImage):
    border_type = BorderType(CEBorderType(CEBorderType.standoff))


class Section(StationObjectImage):
    border_points = SectBorderPoints("complex_type")


class StationObjectsStorage:
    def __init__(self):
        """ reimplement for OrderedDict[str, OrderedDict[str, SO]] """
        self.name_to_object: OrderedDict[str, StationObjectImage] = OrderedDict()
        self.class_objects = OrderedDict.fromkeys([cls.__name__ for cls in StationObjectImage.__subclasses__()], copy([]))

        self.add_new_object(CoordinateSystem(), "GlobalCS")

    def add_new_object(self, obj: StationObjectImage, name: str = None):
        if name:
            assert isinstance(obj, CoordinateSystem) and (name == "GlobalCS"), "Parameter only for GCS"
        else:
            name = obj.name
        self.class_objects[obj.__class__.__name__].append(name)
        self.name_to_object[name] = obj


SOS = StationObjectsStorage()

if __name__ == "__main__":
    test_1 = True
    if test_1:
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
        print(getattr(CsDepend, "__set__") == BaseAttrDescriptor.__set__)
        print(getattr(RailPDirMinusPoint, "__set__") == BaseAttrDescriptor.__set__)
        cs.cs_relative_to = "GlobalCS"
        cs.x = "35"
        cs.co_x = "false"

        for attr in cs.active_attrs:
            print(getattr(cs, attr))

    test_2 = True
    if test_2:
        pnt = Point()
        pnt.name = "Point"
        pnt.on = "line"
        SOS.add_new_object(pnt)
        for attr in pnt.active_attrs:
            print(getattr(pnt, attr))
        ax = Axis()
        ax.creation_method = "rotational"
        print()
        ax.center_point = "Point"
        for attr in ax.active_attrs:
            print(getattr(ax, attr))
