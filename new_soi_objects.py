from __future__ import annotations
from typing import Type, Union, Iterable
from collections import OrderedDict
from copy import copy

from custom_enum import CustomEnum
from enums_images import CEDependence, CEBool, CEAxisCreationMethod, CEAxisOrLine, CELightRouteType, CELightStickType, \
    CEBorderType, CELightColor
from picket_coordinate import PicketCoordinate
from default_ordered_dict import DefaultOrderedDict

from config_names import GLOBAL_CS_NAME


# class AttributeEvaluateError(Exception):
#     pass
#
#
# class AERequiredAttributeError(AttributeEvaluateError):
#     pass
#
#
# class AEObjectNotFoundError(AttributeEvaluateError):
#     pass
#
#
# class AETypeAttributeError(AttributeEvaluateError):
#     pass


# ------------        ORIGINAL DESCRIPTORS        ------------ #


class SOIAttrSeqTemplate:
    def __get__(self, instance, owner) -> list[str]:

        return [attr_name for attr_name in owner.__dict__ if not attr_name.startswith("__")]

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


class SODictEnumPossibleValues:
    def __get__(self, instance, owner) -> OrderedDict[str, list[str]]:
        result = OrderedDict()
        for attr_ in owner.attr_sequence_template:
            attrib = getattr(owner, attr_)
            if attrib.enum:
                result[attr_] = attrib.enum.possible_values
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


# ------------        BASE SOI-ATTRIBUTE DESCRIPTORS        ------------ #

class BaseDescriptor:
    """ Contains single value or list of values """

    def __init__(self, count_requirement: int = 1):
        self.count_requirement = count_requirement

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if not instance:
            return self
        elif hasattr(instance, "_{}".format(self.name)):
            return getattr(instance, "_{}".format(self.name))
        else:
            if self.count_requirement == 1:
                setattr(instance, "_{}".format(self.name), "")
                setattr(instance, "_str_{}".format(self.name), "")
                setattr(instance, "_check_status_{}".format(self.name), "")
            elif self.count_requirement == -1:
                setattr(instance, "_{}".format(self.name), [""] * 1)
                setattr(instance, "_str_{}".format(self.name), [""] * 1)
                setattr(instance, "_check_status_{}".format(self.name), [""] * 1)
            else:
                setattr(instance, "_{}".format(self.name), [""] * self.count_requirement)
                setattr(instance, "_str_{}".format(self.name), [""] * self.count_requirement)
                setattr(instance, "_check_status_{}".format(self.name), [""] * self.count_requirement)
            return getattr(instance, "_{}".format(self.name))

    def __set__(self, instance: StationObjectImage, value: Union[str, list[str]]):
        setattr(instance, "_str_"+self.name, value)


class IntTypeDescriptor(BaseDescriptor):
    """ Contains standard value as int, float, str """

    def __init__(self, count_requirement: int = 1):
        super().__init__(count_requirement)

    def __set__(self, instance: StationObjectImage, input_value: Union[str, list[str]]):
        super().__set__(instance, input_value)
        if isinstance(input_value, str):
            input_value = input_value.strip()
        else:
            input_value = [val.strip() for val in input_value]
        if isinstance(input_value, str):
            if input_value.isdigit() and (self.count_requirement == 1):
                setattr(instance, "_"+self.name, input_value)
                setattr(instance, "_check_status_"+self.name, "")
            else:
                setattr(instance, "_check_status_"+self.name, "Value {} is not single int".format(input_value))
        else:
            if not hasattr(instance, "_{}".format(self.name)):
                if self.count_requirement == -1:
                    setattr(instance, "_{}".format(self.name), [""] * 1)
                else:
                    setattr(instance, "_{}".format(self.name), [""] * self.count_requirement)
            old_destination_list = getattr(instance, "_{}".format(self.name))
            destination_list = []
            check_list = []
            for i, value in enumerate(input_value):
                destination_list.append("")
                check_list.append("")
                if value.isdigit():
                    destination_list[-1] = value
                    check_list[-1] = ""
                else:
                    check_list[-1] = "Value {} is not int".format(value)
                    if i < len(old_destination_list):
                        destination_list[i] = old_destination_list[i]
            setattr(instance, "_{}".format(self.name), destination_list)
            setattr(instance, "_check_status_{}".format(self.name), check_list)


class BoundedSetOfValuesDescriptor(BaseDescriptor):

    def __init__(self, count_requirement: int = 1):
        super().__init__(count_requirement)
        self._possible_values = []

    def __set__(self, instance: StationObjectImage, input_value: Union[str, list[str]]):
        super().__set__(instance, input_value)
        if isinstance(input_value, str):
            input_value = input_value.strip()
        else:
            input_value = [val.strip() for val in input_value]
        if isinstance(input_value, str):
            if (input_value in self.possible_values) and (self.count_requirement == 1):
                setattr(instance, "_"+self.name, input_value)
                setattr(instance, "_check_status_"+self.name, "")
            else:
                setattr(instance, "_check_status_"+self.name,
                        "Value {} not in list of possible values: {}".format(input_value, self.possible_values))
        else:
            if not hasattr(instance, "_{}".format(self.name)):
                if self.count_requirement == -1:
                    setattr(instance, "_{}".format(self.name), [""] * 1)
                else:
                    setattr(instance, "_{}".format(self.name), [""] * self.count_requirement)
            old_destination_list = getattr(instance, "_{}".format(self.name))
            destination_list = []
            check_list = []
            for i, value in enumerate(input_value):
                destination_list.append("")
                check_list.append("")
                if value in self.possible_values:
                    destination_list[-1] = value
                    check_list[-1] = ""
                else:
                    check_list[-1] = "Value {} not in list of possible values: {}".format(value,
                                                                                          self.possible_values)
                    if i < len(old_destination_list):
                        destination_list[i] = old_destination_list[i]
            setattr(instance, "_{}".format(self.name), destination_list)
            setattr(instance, "_check_status_{}".format(self.name), check_list)

    @property
    def possible_values(self) -> list[str]:
        result = list(self._possible_values)
        return result

    @possible_values.setter
    def possible_values(self, values: Iterable[str]):
        self._possible_values = values


# ------------        IMAGE OBJECTS CLASSES        ------------ #

class StationObjectImage:
    attr_sequence_template = SOIAttrSeqTemplate()
    active_attrs = SOIActiveAttrs()
    odict_enum_possible_values = SODictEnumPossibleValues()
    odict_values = SOIListValues()
    name = SOIName()


class CoordinateSystemSOI(StationObjectImage):
    cs_relative_to = BoundedSetOfValuesDescriptor()
    dependence = BoundedSetOfValuesDescriptor()
    x = IntTypeDescriptor()
    co_x = BoundedSetOfValuesDescriptor()
    co_y = BoundedSetOfValuesDescriptor()


class AxisSOI(StationObjectImage):
    cs_relative_to = BoundedSetOfValuesDescriptor()
    creation_method = BoundedSetOfValuesDescriptor()
    y = IntTypeDescriptor()
    center_point = BoundedSetOfValuesDescriptor()
    alpha = IntTypeDescriptor()


class PointSOI(StationObjectImage):
    on = BoundedSetOfValuesDescriptor()
    axis = BoundedSetOfValuesDescriptor()
    line = BoundedSetOfValuesDescriptor()
    cs_relative_to = BoundedSetOfValuesDescriptor()
    x = IntTypeDescriptor()


class LineSOI(StationObjectImage):
    points = BoundedSetOfValuesDescriptor(count_requirement=2)


class LightSOI(StationObjectImage):
    light_route_type = BoundedSetOfValuesDescriptor()
    center_point = BoundedSetOfValuesDescriptor()
    direct_point = BoundedSetOfValuesDescriptor()
    colors = BoundedSetOfValuesDescriptor(count_requirement=-1)
    light_stick_type = BoundedSetOfValuesDescriptor()


class RailPointSOI(StationObjectImage):
    center_point = BoundedSetOfValuesDescriptor()
    dir_plus_point = BoundedSetOfValuesDescriptor()
    dir_minus_point = BoundedSetOfValuesDescriptor()


class BorderSOI(StationObjectImage):
    point = BoundedSetOfValuesDescriptor()
    border_type = BoundedSetOfValuesDescriptor()


class SectionSOI(StationObjectImage):
    border_points = BoundedSetOfValuesDescriptor(count_requirement=-1)


if __name__ == "__main__":
    test_1 = False
    if test_1:
        cs = CoordinateSystemSOI()
        cs.cs_relative_to = "Global"
        print(cs._str_cs_relative_to)
        cs_2 = copy(cs)
        cs.cs_relative_to = "NonGlobal"
        print(cs._str_cs_relative_to)
        print(cs_2._str_cs_relative_to)
        print(cs, cs_2)

    test_2 = False
    if test_2:
        cs = CoordinateSystemSOI()
        print(cs.attr_sequence_template)
        print(CoordinateSystemSOI.odict_enum_possible_values)
        cs.dependence = 'dependent'
        print(cs.active_attrs)
        print(cs.odict_values)

    test_3 = False
    if test_3:
        pass