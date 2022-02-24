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
from attribute_data import AttributeData

from config_names import GLOBAL_CS_NAME


class AttributeEvaluateError(Exception):
    pass


class AEEnumValueAttributeError(AttributeEvaluateError):
    pass


class AEObjectNotFoundError(AttributeEvaluateError):
    pass


class AERequiredAttributeError(AttributeEvaluateError):
    pass


class AETypeAttributeError(AttributeEvaluateError):
    pass


# ------------        ORIGINAL DESCRIPTORS        ------------ #

# class SOIName:
#     def __get__(self, instance, owner):
#         assert instance, "Only for instance"
#         return getattr(instance, "_name")
#
#     def __set__(self, instance, value: str):
#         instance._name = value


# ------------        BASE SOI-ATTRIBUTE DESCRIPTORS        ------------ #


# ------------        IMAGE OBJECTS CLASSES        ------------ #

class ChangeAttribList:
    def __init__(self, attr_value_add_dict: OrderedDict[str, list[str]]):
        self.attr_value_add_dict = attr_value_add_dict

    @property
    def preferred_value(self):
        return list(self.attr_value_add_dict.keys())[0]

    def add_list(self, attr_value):
        return self.attr_value_add_dict[attr_value]

    def remove_list(self, attr_value):
        result = []
        for attr_val in self.attr_value_add_dict:
            if attr_val != attr_value:
                result.extend(self.attr_value_add_dict[attr_val])
        return result


@dataclass
class AttribProperties:
    last_input_value: str = ""
    confirmed_value: Any = ""
    str_confirmed_value: str = ""
    suggested_value: str = ""

    # is_required: str = ""
    # count_requirement: str = ""
    # min_count: str = ""
    # exactly_count: str = ""
    # check_status: str = ""


@dataclass
class IndexManagementCommand:
    command: str
    index: int = -1


class UniversalDescriptor:

    def __init__(self, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1):
        self.is_required = is_required
        self.is_list = is_list
        assert (min_count == -1) or (exactly_count == -1)
        self.min_count = min_count
        self.exactly_count = exactly_count

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner) -> Union[UniversalDescriptor, AttribProperties, list[AttribProperties]]:
        if not instance:
            return self
        return getattr(instance, "_{}".format(self.name))

    def __set__(self, instance, value: tuple[Union[str, list[str]], bool, Optional[IndexManagementCommand]]):
        ad = AttributeData(instance.__class__.__name__, instance.name, self.name)
        check_mode = value[1]
        if not self.is_list:
            assert isinstance(value[0], str)
            str_value = value[0].strip()
            if not hasattr(instance, "_{}".format(self.name)):
                ap_for_handle = AttribProperties()
                setattr(instance, "_{}".format(self.name), ap_for_handle)
            else:
                ap_for_handle = getattr(instance, "_{}".format(self.name))
            self.handling_ap(ap_for_handle, str_value, check_mode, ad)
        else:
            assert len(value) == 3
            command = value[2].command
            index = value[2].index
            # print("in set", value)
            # print("in set", instance.__class__.__name__, instance.name, self.name, command, index)

            if not hasattr(instance, "_{}".format(self.name)):
                setattr(instance, "_{}".format(self.name), [])
            old_ap_list: list[AttribProperties] = getattr(instance, "_{}".format(self.name))
            if command in ["remove_index", "append", "set_index"]:
                str_value = value[0].strip()
                if command == "remove_index":
                    old_ap_list.pop(index)
                    return
                if command == "append":
                    ap_for_handle = AttribProperties()
                    old_ap_list.append(ap_for_handle)
                if command == "set_index":
                    ad.index = index
                    ap_for_handle = old_ap_list[index]
                self.handling_ap(ap_for_handle, str_value, check_mode, ad)
            elif command == "set_list":
                old_ap_list.clear()
                str_list: list[str] = value[0]
                for i, str_value in enumerate(str_list):
                    ad = AttributeData(instance.__class__.__name__, instance.name, self.name)
                    ad.index = i
                    str_value = str_value.strip()
                    ap_for_handle = AttribProperties()
                    self.handling_ap(ap_for_handle, str_value, check_mode, ad)
                    old_ap_list.append(ap_for_handle)

    def handling_ap(self, ap: AttribProperties, new_str_value: str, check_mode: bool, ad: AttributeData):
        ap.last_input_value = new_str_value


class EnumDescriptor(UniversalDescriptor):

    def __init__(self, possible_values: list[str] = None, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count)
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

    def handling_ap(self, ap: AttribProperties, new_str_value: str, check_mode: bool, ad: AttributeData):
        super().handling_ap(ap, new_str_value, check_mode, ad)
        if new_str_value:  #  and self.possible_values
            if new_str_value not in self.possible_values:
                raise AEEnumValueAttributeError("Value '{}' not in possible list: '{}'".format(new_str_value,
                                                                                           self.possible_values), ad)
            ap.confirmed_value = new_str_value
            ap.str_confirmed_value = new_str_value


class StationObjectDescriptor(UniversalDescriptor):

    def __init__(self, contains_cls_name: str, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count)
        self.contains_cls_name = contains_cls_name
        self._obj_dict = OrderedDict()

    @property
    def obj_dict(self) -> OrderedDict[str, StationObjectImage]:
        return self._obj_dict

    @obj_dict.setter
    def obj_dict(self, odict: OrderedDict[str, StationObjectImage]):
        self._obj_dict = odict

    def handling_ap(self, ap: AttribProperties, new_str_value: str, check_mode: bool, ad: AttributeData):
        super().handling_ap(ap, new_str_value, check_mode, ad)
        if new_str_value and check_mode:
            if new_str_value not in self.obj_dict:
                print("ad", ad)
                raise AEObjectNotFoundError("Object '{}' not found in class '{}'".format(new_str_value,
                                                                                         self.contains_cls_name), ad)
            ap.confirmed_value = self.obj_dict[new_str_value]
            ap.str_confirmed_value = new_str_value


class IntDescriptor(UniversalDescriptor):

    def __init__(self, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count)

    def handling_ap(self, ap: AttribProperties, new_str_value: str, check_mode: bool, ad: AttributeData):
        super().handling_ap(ap, new_str_value, check_mode, ad)
        if new_str_value:
            try:
                ap.confirmed_value = int(new_str_value)
                ap.str_confirmed_value = new_str_value
            except ValueError:
                raise AETypeAttributeError("Value '{}' is not int".format(new_str_value), ad)


class PicketDescriptor(UniversalDescriptor):

    def __init__(self, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count)

    def handling_ap(self, ap: AttribProperties, new_str_value: str, check_mode: bool, ad: AttributeData):
        super().handling_ap(ap, new_str_value, check_mode, ad)
        if new_str_value:
            try:
                ap.confirmed_value = PicketCoordinate(new_str_value).value
                ap.str_confirmed_value = new_str_value
            except PicketCoordinateParsingCoError:
                raise AETypeAttributeError("Value '{}' is not picket coordinate".format(new_str_value), ad)


class StationObjectImage:
    # name = SOIName()

    def __init__(self):
        self.name = ""
        self.active_attrs: list[str] = [attr_name for attr_name in self.__class__.__dict__
                                        if not attr_name.startswith("__")]
        # all attrs initialization
        for attr_name in self.active_attrs:
            descr: UniversalDescriptor = getattr(self.__class__, attr_name)
            if not descr.is_list:
                setattr(self, attr_name, ("", False))
            else:
                if descr.min_count != -1:
                    for _ in range(descr.min_count):
                        setattr(self, attr_name, ("", False, IndexManagementCommand(command="append")))
                if descr.exactly_count != -1:
                    for _ in range(descr.exactly_count):
                        setattr(self, attr_name, ("", False, IndexManagementCommand(command="append")))

        # switch attrs initialization
        if self.__class__ in SWITCH_ATTR_LISTS:
            for attr_name in SWITCH_ATTR_LISTS[self.__class__]:
                chal: ChangeAttribList = SWITCH_ATTR_LISTS[self.__class__][attr_name]
                # print("preferred_value", chal.preferred_value)
                self.change_attrib_value(attr_name, chal.preferred_value)
        # print("init success")

    """ interface attribute setter """
    def change_attrib_value(self, attr_name: str, attr_value: Union[str, list[str]], index: int = -1,
                            check_mode: bool = True):

        # set attr
        if attr_name == "name":
            setattr(self, attr_name, attr_value)
            return
        else:
            descr: UniversalDescriptor = getattr(self.__class__, attr_name)
            if not descr.is_list:
                assert isinstance(attr_value, str)
                setattr(self, attr_name, (attr_value, check_mode))
            elif index == -1:
                if isinstance(attr_value, str):
                    attr_value = [attr_value]
                setattr(self, attr_name, (attr_value, check_mode, IndexManagementCommand(command="set_list")))
            else:
                setattr(self, attr_name, (attr_value, check_mode, IndexManagementCommand(command="set_index", index=index)))

        # switch attr
        if (self.__class__ in SWITCH_ATTR_LISTS) and (attr_name in SWITCH_ATTR_LISTS[self.__class__]):
            chal: ChangeAttribList = SWITCH_ATTR_LISTS[self.__class__][attr_name]
            for remove_value in chal.remove_list(attr_value):
                if remove_value in self.active_attrs:
                    self.active_attrs.remove(remove_value)
            index_insert = self.active_attrs.index(attr_name) + 1
            for add_value in reversed(chal.add_list(attr_value)):
                if add_value not in self.active_attrs:
                    self.active_attrs.insert(index_insert, add_value)

    def reload_attr_value(self, attr_name: str):
        attr_prop_values = getattr(self, attr_name)
        if isinstance(attr_prop_values, AttribProperties):
            self.change_attrib_value(attr_name, attr_prop_values.last_input_value)
        else:
            self.change_attrib_value(attr_name, self.list_attr_input_value(attr_name))

    """ interface list attribute input str getter """
    def list_attr_input_value(self, attr_name: str):
        attr_prop_values = getattr(self, attr_name)
        if isinstance(attr_prop_values, AttribProperties):
            attr_prop_values = [attr_prop_values]
        return [apv.last_input_value for apv in attr_prop_values]

    def single_attr_input_value(self, attr_name: str, index: int = -1):
        if attr_name == "name":
            return self.name
        laiv = self.list_attr_input_value(attr_name)
        return laiv[index] if index != -1 else laiv[0]

    """ interface list attribute str confirmed value getter """
    def list_attr_str_confirmed_value(self, attr_name: str):
        attr_prop_values = getattr(self, attr_name)
        if isinstance(attr_prop_values, AttribProperties):
            attr_prop_values = [attr_prop_values]
        return [apv.str_confirmed_value for apv in attr_prop_values]

    """ interface list attribute str suggested value getter """
    def list_attr_str_suggested_value(self, attr_name: str):
        attr_prop_values = getattr(self, attr_name)
        if isinstance(attr_prop_values, AttribProperties):
            attr_prop_values = [attr_prop_values]
        return [apv.suggested_value for apv in attr_prop_values]

    """ interface list attribute confirmed value getter """
    def attr_confirmed_value(self, attr_name: str):
        attr_prop_values = getattr(self, attr_name)
        if isinstance(attr_prop_values, AttribProperties):
            return attr_prop_values.confirmed_value
        else:
            return [attr_prop_value.confirmed_value for attr_prop_value in attr_prop_values]


class CoordinateSystemSOI(StationObjectImage):
    dependence = EnumDescriptor(CEDependence.possible_values)
    cs_relative_to = StationObjectDescriptor("CoordinateSystemSOI")
    x = IntDescriptor()
    co_x = EnumDescriptor(CEBool.possible_values)
    co_y = EnumDescriptor(CEBool.possible_values)


class AxisSOI(StationObjectImage):
    cs_relative_to = StationObjectDescriptor("CoordinateSystemSOI")
    creation_method = EnumDescriptor(CEAxisCreationMethod.possible_values)
    y = IntDescriptor()
    center_point = StationObjectDescriptor("PointSOI")
    alpha = IntDescriptor()


class PointSOI(StationObjectImage):
    on = EnumDescriptor(CEAxisOrLine.possible_values)
    axis = StationObjectDescriptor("AxisSOI")
    line = StationObjectDescriptor("LineSOI")
    cs_relative_to = StationObjectDescriptor("CoordinateSystemSOI")
    x = PicketDescriptor()


class LineSOI(StationObjectImage):
    points = StationObjectDescriptor("PointSOI", is_list=True)


class LightSOI(StationObjectImage):
    light_route_type = EnumDescriptor(CELightRouteType.possible_values)
    center_point = StationObjectDescriptor("PointSOI")
    direct_point = StationObjectDescriptor("PointSOI")
    colors = EnumDescriptor(CELightColor.possible_values, is_list=True)
    light_stick_type = EnumDescriptor(CELightStickType.possible_values)


class RailPointSOI(StationObjectImage):
    center_point = StationObjectDescriptor("PointSOI")
    dir_plus_point = StationObjectDescriptor("PointSOI")
    dir_minus_point = StationObjectDescriptor("PointSOI")


class BorderSOI(StationObjectImage):
    point = StationObjectDescriptor("PointSOI")
    border_type = EnumDescriptor(CEBorderType.possible_values)


class SectionSOI(StationObjectImage):
    border_points = StationObjectDescriptor("PointSOI", is_list=True)


SWITCH_ATTR_LISTS = {CoordinateSystemSOI: {"dependence": ChangeAttribList(OrderedDict({"independent": [],
                                                                                       "dependent": [
                                                                                           "cs_relative_to",
                                                                                           "x",
                                                                                           "co_x",
                                                                                           "co_y"]}))},
                     AxisSOI: {"creation_method": ChangeAttribList(OrderedDict({"rotational": [
                         "center_point",
                         "alpha"],
                         "translational": ["y"]}))},
                     PointSOI: {"on": ChangeAttribList(OrderedDict({"axis": ["axis"],
                                                                    "line": ["line"]}))}
                     }

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
        cs.change_attrib_value("dependence", "dependent")
        print(cs.active_attrs)
        cs.change_attrib_value("dependence", "independent")
        print(cs.active_attrs)
        cs.change_attrib_value("dependence", "dependent")
        print(cs.active_attrs)
        print("attr_values", [(active_attr, getattr(cs, active_attr)) for active_attr in cs.active_attrs])

        cs = AxisSOI()
        # cs.creation_method
        print(cs.active_attrs)
        cs.change_attrib_value("creation_method", "translational")
        print(cs.active_attrs)
        cs.change_attrib_value("creation_method", "rotational")
        print(cs.active_attrs)
        cs.change_attrib_value("creation_method", "translational")
        print(cs.active_attrs)

        cs = PointSOI()
        # cs.creation_method
        print(cs.active_attrs)
        cs.change_attrib_value("on", "axis")
        print(cs.active_attrs)
        cs.change_attrib_value("on", "line")
        print(cs.active_attrs)
        cs.change_attrib_value("on", "axis")
        print(cs.active_attrs)

        cs = BorderSOI()
        # cs.creation_method
        print(cs.active_attrs)
