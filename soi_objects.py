from __future__ import annotations
from typing import Type, Union, Iterable, Any, Optional
from collections import OrderedDict
from copy import copy
from dataclasses import dataclass

from custom_enum import CustomEnum
from enums_images import CEDependence, CEBool, CEAxisCreationMethod, CEAxisOrLine, CELightRouteType, CELightStickType, \
    CEBorderType, CELightColor
from picket_coordinate import PicketCoordinate, PicketCoordinateParsingCoError
from default_ordered_dict import DefaultOrderedDict
# from attrib_properties import AttribProperties
# from attrib_index import CompositeAttributeIndex
from attribute_object_key import AttributeKey
from soi_metadata import ClassProperties, ObjectProperties, ComplexAttribProperties, \
    SingleAttribProperties
from form_exception_message import form_message_from_error

from config_names import GLOBAL_CS_NAME


class AttributeEvaluateError(Exception):
    pass


""" complex_attr exceptions """


class ComplexAttrError(Exception):
    pass


class NotFoundComplexAttrError(ComplexAttrError):
    pass


class ManyFoundComplexAttrError(ComplexAttrError):
    pass


""" name exceptions """


class NameEvaluateError(Exception):
    pass


class AENameRepeatingError(NameEvaluateError):
    pass


class AENameNotIdentifierError(NameEvaluateError):
    pass


class AENameEmptyError(NameEvaluateError):
    pass


""" enum exceptions """


class AEEnumValueAttributeError(AttributeEvaluateError):
    pass


""" object exceptions """


class AEObjectNotFoundError(AttributeEvaluateError):
    pass


class AERequiredAttributeError(AttributeEvaluateError):
    pass


class AETypeAttributeError(AttributeEvaluateError):
    pass


@dataclass
class AttribValues:
    last_input_value: str = ""
    confirmed_value: Any = ""
    str_confirmed_value: str = ""


@dataclass
class IndexManagementCommand:
    command: str
    index: int = -1


class UniversalDescriptor:

    def __init__(self, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exact_count: int = -1, immutable: bool = False):
        self.is_required = is_required
        self.is_list = is_list
        assert (min_count == -1) or (exact_count == -1)
        self.min_count = min_count
        self.exact_count = exact_count
        self.immutable = immutable

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if not instance:
            return self
        return getattr(instance, "_{}".format(self.name))

    def __set__(self, instance, value: Union[str, tuple[Union[str, list[str]], Optional[IndexManagementCommand]]]):
        if not self.is_list:
            assert isinstance(value, str)
            str_value = value.strip()
            setattr(instance, "_{}".format(self.name), self.handling_ap(str_value))
        else:
            assert isinstance(value, tuple)
            assert len(value) == 2
            command = value[1].command
            index = value[1].index
            old_values_list: list = getattr(instance, "_{}".format(self.name))
            if command == "remove_index":
                old_values_list.pop(index)
            elif command == "set_index":
                str_value = value[0].strip()
                assert index <= len(old_values_list)
                if index == len(old_values_list):
                    old_values_list.append(self.handling_ap(str_value))
                else:
                    old_values_list[index] = self.handling_ap(str_value)
            else:
                assert False

    def handling_ap(self, new_str_value: str):
        pass


class EnumDescriptor(UniversalDescriptor):

    def __init__(self, possible_values: list[str] = None, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exact_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exact_count=exact_count,
                         immutable=immutable)
        if not possible_values:
            self._possible_values = []
        else:
            self._possible_values = possible_values

    @property
    def possible_values(self) -> list[str]:
        return self._possible_values

    @possible_values.setter
    def possible_values(self, values: Iterable[str]):
        self._possible_values = list(values)

    def handling_ap(self, new_str_value: str) -> str:
        if new_str_value not in self.possible_values:
            raise AEEnumValueAttributeError("Value '{}' not in possible list: '{}'".format(new_str_value,
                                                                                           self.possible_values))
        return new_str_value


class StationObjectDescriptor(UniversalDescriptor):

    def __init__(self, contains_cls_name: str, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exact_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exact_count=exact_count,
                         immutable=immutable)
        self.contains_cls_name = contains_cls_name
        self._obj_dict = OrderedDict()

    @property
    def obj_dict(self) -> OrderedDict[str, StationObjectImage]:
        return self._obj_dict

    @obj_dict.setter
    def obj_dict(self, odict: OrderedDict[str, StationObjectImage]):
        self._obj_dict = odict

    def handling_ap(self, new_str_value: str) -> StationObjectImage:
        # print("obj_dict", self.obj_dict)
        if new_str_value not in self.obj_dict:
            raise AEObjectNotFoundError("Object '{}' not found in class '{}'".format(new_str_value,
                                                                                     self.contains_cls_name))
        return self.obj_dict[new_str_value]


class IntDescriptor(UniversalDescriptor):

    def __init__(self, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exact_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exact_count=exact_count,
                         immutable=immutable)

    def handling_ap(self, new_str_value: str) -> int:
        try:
            return int(new_str_value)
        except ValueError:
            raise AETypeAttributeError("Value '{}' is not int".format(new_str_value))


class PicketDescriptor(UniversalDescriptor):

    def __init__(self, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exact_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exact_count=exact_count,
                         immutable=immutable)

    def handling_ap(self, new_str_value: str) -> int:
        super().handling_ap(new_str_value)
        try:
            return PicketCoordinate(new_str_value).value
        except PicketCoordinateParsingCoError:
            raise AETypeAttributeError("Value '{}' is not picket coordinate".format(new_str_value))


class NameDescriptor(UniversalDescriptor):

    def __init__(self, contains_cls_name: str, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exact_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exact_count=exact_count,
                         immutable=immutable)
        self.contains_cls_name = contains_cls_name
        self._obj_dict = OrderedDict()

    @property
    def obj_dict(self) -> OrderedDict[str, StationObjectImage]:
        return self._obj_dict

    @obj_dict.setter
    def obj_dict(self, odict: OrderedDict[str, StationObjectImage]):
        self._obj_dict = odict

    def handling_ap(self, new_str_value: str) -> str:
        # print("")
        if (not new_str_value) or new_str_value.isspace():
            raise AENameEmptyError("Name is empty")
        if not new_str_value.replace("_", "").isalnum():
            raise AENameNotIdentifierError("Name '{}' is not valid identifier".format(new_str_value))
        if new_str_value in self.obj_dict:
            raise AENameRepeatingError("Name '{}' repeats in class '{}'".format(new_str_value,
                                                                                self.contains_cls_name))
        return new_str_value

    def make_name_suggestion(self) -> str:
        i = 0
        while True:
            i += 1
            candid_name = "{}_{}".format(self.contains_cls_name.replace("SOI", ""), i)
            if candid_name not in self.obj_dict:
                break
        return candid_name


class StationObjectImage:
    name = ""

    def __init__(self):
        self.object_prop_struct: ObjectProperties = ObjectProperties()
        self.init_list_descriptors()
        self.init_object_prop_struct()

    def init_object_prop_struct(self):
        obj_prop = self.object_prop_struct
        cls = self.__class__
        for attr_name in [key for key in cls.__dict__.keys() if not key.startswith("__")]:
            complex_attr = ComplexAttribProperties()
            obj_prop.attrib_list.append(complex_attr)
            descriptor: UniversalDescriptor = getattr(cls, attr_name)
            complex_attr.name = attr_name
            complex_attr.is_list = descriptor.is_list
            complex_attr.min_count = descriptor.min_count
            complex_attr.exact_count = descriptor.exact_count
            complex_attr.immutable = descriptor.immutable
            if complex_attr.min_count != -1:
                for index in range(complex_attr.min_count):
                    self.append_complex_attr_index(attr_name)
            if complex_attr.exact_count != -1:
                for index in range(complex_attr.exact_count):
                    self.append_complex_attr_index(attr_name)

    def init_list_descriptors(self):
        cls = self.__class__
        for attr_name in [key for key in cls.__dict__.keys() if not key.startswith("__")]:
            descriptor: UniversalDescriptor = getattr(cls, attr_name)
            if descriptor.is_list:
                setattr(self, "_{}".format(attr_name), [])

    def append_complex_attr_index(self, attr_name: str):
        complex_attr = self.get_complex_attr_prop(attr_name)
        single_attr = SingleAttribProperties()
        if complex_attr.is_list:
            single_attr.index = len(complex_attr.single_attr_list)
            complex_attr.single_attr_list.append(single_attr)
            # setattr(self, attr_name, ("", IndexManagementCommand(command="append")))
        else:
            assert not complex_attr.single_attr_list
            single_attr.index = -1
            complex_attr.single_attr_list.append(single_attr)
            # setattr(self, attr_name, "")

    def remove_complex_attr_index(self, attr_name: str, index: int):
        complex_attr = self.get_complex_attr_prop(attr_name)
        complex_attr.single_attr_list.pop(index)

    def remove_descriptor_index(self, attr_name: str, index: int):
        setattr(self, attr_name, ("", IndexManagementCommand(command="remove_index", index=index)))

    def get_complex_attr_prop(self, attr_name: str) -> ComplexAttribProperties:
        result_list = []
        for complex_attr_prop_candidate in self.object_prop_struct.attrib_list:
            if complex_attr_prop_candidate.name == attr_name:
                result_list.append(complex_attr_prop_candidate)
        if not result_list:
            raise NotFoundComplexAttrError("Attr '{}' not found in object".format(attr_name))
        if len(result_list) > 1:
            raise ManyFoundComplexAttrError("More then 1 '{}' found in object".format(attr_name))
        return result_list.pop()

    def get_single_attr_prop(self, attr_name: str, index: int = -1) -> SingleAttribProperties:
        result_list = []
        complex_attr_prop = self.get_complex_attr_prop(attr_name)
        for single_attr_prop_candidate in complex_attr_prop.single_attr_list:
            if single_attr_prop_candidate.index == index:
                result_list.append(single_attr_prop_candidate)
        assert result_list, "Attr not found"
        assert len(result_list) < 2, "More then 1 found"
        return result_list.pop()

    @property
    def active_complex_attrs(self) -> list[ComplexAttribProperties]:
        return [complex_attr for complex_attr in self.object_prop_struct.attrib_list if complex_attr.active]

    @property
    def active_attr_names(self) -> list[str]:
        return [complex_attr.name for complex_attr in self.active_complex_attrs]

    # def from_temporary_to_stable(self):
    #     for complex_attr_prop_candidate in self.object_prop_struct.attrib_list:
    #         pass


class CoordinateSystemSOI(StationObjectImage):
    name = NameDescriptor("CoordinateSystem")
    dependence = EnumDescriptor(CEDependence.possible_values)
    cs_relative_to = StationObjectDescriptor("CoordinateSystem")
    x = IntDescriptor()
    co_x = EnumDescriptor(CEBool.possible_values)
    co_y = EnumDescriptor(CEBool.possible_values)


class AxisSOI(StationObjectImage):
    name = NameDescriptor("Axis")
    cs_relative_to = StationObjectDescriptor("CoordinateSystem")
    creation_method = EnumDescriptor(CEAxisCreationMethod.possible_values)
    y = IntDescriptor()
    center_point = StationObjectDescriptor("Point")
    alpha = IntDescriptor()


class PointSOI(StationObjectImage):
    name = NameDescriptor("Point")
    on = EnumDescriptor(CEAxisOrLine.possible_values)
    axis = StationObjectDescriptor("Axis")
    line = StationObjectDescriptor("Line")
    cs_relative_to = StationObjectDescriptor("CoordinateSystem")
    x = PicketDescriptor()


class LineSOI(StationObjectImage):
    name = NameDescriptor("Line")
    points = StationObjectDescriptor("Point", is_list=True, exact_count=2)


class LightSOI(StationObjectImage):
    name = NameDescriptor("Light")
    light_route_type = EnumDescriptor(CELightRouteType.possible_values)
    center_point = StationObjectDescriptor("Point")
    direct_point = StationObjectDescriptor("Point")
    colors = EnumDescriptor(CELightColor.possible_values, is_list=True, min_count=1)
    light_stick_type = EnumDescriptor(CELightStickType.possible_values)


class RailPointSOI(StationObjectImage):
    name = NameDescriptor("RailPoint")
    center_point = StationObjectDescriptor("Point")
    dir_plus_point = StationObjectDescriptor("Point")
    dir_minus_point = StationObjectDescriptor("Point")


class BorderSOI(StationObjectImage):
    name = NameDescriptor("Border")
    point = StationObjectDescriptor("Point")
    border_type = EnumDescriptor(CEBorderType.possible_values)


class SectionSOI(StationObjectImage):
    name = NameDescriptor("Section")
    border_points = StationObjectDescriptor("Point", is_list=True, min_count=2)


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

    test_3 = True
    if test_3:
        cs = CoordinateSystemSOI()
        print(cs.active_attrs)
        cs.change_single_attrib_value("dependence", "dependent")
        print(cs.active_attrs)
        cs.change_single_attrib_value("dependence", "independent")
        print(cs.active_attrs)
        cs.change_single_attrib_value("dependence", "dependent")
        print(cs.active_attrs)
        print("attr_values", [(active_attr, getattr(cs, active_attr)) for active_attr in cs.active_attrs])

        cs = AxisSOI()
        # cs.creation_method
        print(cs.active_attrs)
        cs.change_single_attrib_value("creation_method", "translational")
        print(cs.active_attrs)
        cs.change_single_attrib_value("creation_method", "rotational")
        print(cs.active_attrs)
        cs.change_single_attrib_value("creation_method", "translational")
        print(cs.active_attrs)

        cs = PointSOI()
        # cs.creation_method
        print(cs.active_attrs)
        cs.change_single_attrib_value("on", "axis")
        print(cs.active_attrs)
        cs.change_single_attrib_value("on", "line")
        print(cs.active_attrs)
        cs.change_single_attrib_value("on", "axis")
        print(cs.active_attrs)

        cs = BorderSOI()
        # cs.creation_method
        print(cs.active_attrs)
