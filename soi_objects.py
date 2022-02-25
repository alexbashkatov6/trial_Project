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
from attribute_data import AttributeErrorData
from soi_metadata import ClassProperties, ObjectProperties, ComplexAttribProperties, \
    SingleAttribProperties
from form_exception_message import form_message_from_error

from config_names import GLOBAL_CS_NAME


class AttributeEvaluateError(Exception):
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

# class ChangeAttribList:
#     def __init__(self, attr_value_add_dict: OrderedDict[str, list[str]]):
#         self.attr_value_add_dict = attr_value_add_dict
#
#     @property
#     def preferred_value(self):
#         return list(self.attr_value_add_dict.keys())[0]
#
#     def add_list(self, attr_value):
#         return self.attr_value_add_dict[attr_value]
#
#     def remove_list(self, attr_value):
#         result = []
#         for attr_val in self.attr_value_add_dict:
#             if attr_val != attr_value:
#                 result.extend(self.attr_value_add_dict[attr_val])
#         return result


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
                 min_count: int = -1, exactly_count: int = -1, immutable: bool = False):
        self.is_required = is_required
        self.is_list = is_list
        assert (min_count == -1) or (exactly_count == -1)
        self.min_count = min_count
        self.exactly_count = exactly_count
        self.immutable = immutable

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner) -> Union[UniversalDescriptor, AttribValues, list[AttribValues]]:
        if not instance:
            return self
        return getattr(instance, "_{}".format(self.name))

    def __set__(self, instance, value: tuple[Union[str, list[str]], bool, Optional[IndexManagementCommand]]):
        ad = AttributeErrorData(instance.__class__.__name__, instance.name, self.name)
        check_mode = value[1]
        if not self.is_list:
            assert isinstance(value[0], str)
            str_value = value[0].strip()
            if not hasattr(instance, "_{}".format(self.name)):
                ap_for_handle = AttribValues()
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
            old_ap_list: list[AttribValues] = getattr(instance, "_{}".format(self.name))
            if command in ["remove_index", "append", "set_index"]:
                str_value = value[0].strip()
                if command == "remove_index":
                    old_ap_list.pop(index)
                    return
                if command == "append":
                    ap_for_handle = AttribValues()
                    old_ap_list.append(ap_for_handle)
                if command == "set_index":
                    ad.index = index
                    ap_for_handle = old_ap_list[index]
                self.handling_ap(ap_for_handle, str_value, check_mode, ad)
            elif command == "set_list":
                old_ap_list.clear()
                str_list: list[str] = value[0]
                for i, str_value in enumerate(str_list):
                    ad = AttributeErrorData(instance.__class__.__name__, instance.name, self.name)
                    ad.index = i
                    str_value = str_value.strip()
                    ap_for_handle = AttribValues()
                    self.handling_ap(ap_for_handle, str_value, check_mode, ad)
                    old_ap_list.append(ap_for_handle)

    def handling_ap(self, ap: AttribValues, new_str_value: str, check_mode: bool, ad: AttributeErrorData):
        ap.last_input_value = new_str_value


class EnumDescriptor(UniversalDescriptor):

    def __init__(self, possible_values: list[str] = None, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count,
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

    def handling_ap(self, ap: AttribValues, new_str_value: str, check_mode: bool, ad: AttributeErrorData):
        super().handling_ap(ap, new_str_value, check_mode, ad)
        if new_str_value:  #  and self.possible_values
            if new_str_value not in self.possible_values:
                raise AEEnumValueAttributeError("Value '{}' not in possible list: '{}'".format(new_str_value,
                                                                                           self.possible_values), ad)
            ap.confirmed_value = new_str_value
            ap.str_confirmed_value = new_str_value


class StationObjectDescriptor(UniversalDescriptor):

    def __init__(self, contains_cls_name: str, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count,
                         immutable=immutable)
        self.contains_cls_name = contains_cls_name
        self._obj_dict = OrderedDict()

    @property
    def obj_dict(self) -> OrderedDict[str, StationObjectImage]:
        return self._obj_dict

    @obj_dict.setter
    def obj_dict(self, odict: OrderedDict[str, StationObjectImage]):
        self._obj_dict = odict

    def handling_ap(self, ap: AttribValues, new_str_value: str, check_mode: bool, ad: AttributeErrorData):
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
                 min_count: int = -1, exactly_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count,
                         immutable=immutable)

    def handling_ap(self, ap: AttribValues, new_str_value: str, check_mode: bool, ad: AttributeErrorData):
        super().handling_ap(ap, new_str_value, check_mode, ad)
        if new_str_value:
            try:
                ap.confirmed_value = int(new_str_value)
                ap.str_confirmed_value = new_str_value
            except ValueError:
                raise AETypeAttributeError("Value '{}' is not int".format(new_str_value), ad)


class PicketDescriptor(UniversalDescriptor):

    def __init__(self, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count,
                         immutable=immutable)

    def handling_ap(self, ap: AttribValues, new_str_value: str, check_mode: bool, ad: AttributeErrorData):
        super().handling_ap(ap, new_str_value, check_mode, ad)
        if new_str_value:
            try:
                ap.confirmed_value = PicketCoordinate(new_str_value).value
                ap.str_confirmed_value = new_str_value
            except PicketCoordinateParsingCoError:
                raise AETypeAttributeError("Value '{}' is not picket coordinate".format(new_str_value), ad)


class NameDescriptor(UniversalDescriptor):

    def __init__(self, contains_cls_name: str, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1, immutable: bool = False):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count,
                         immutable=immutable)
        self.contains_cls_name = contains_cls_name
        self._obj_dict = OrderedDict()

    @property
    def obj_dict(self) -> OrderedDict[str, StationObjectImage]:
        return self._obj_dict

    @obj_dict.setter
    def obj_dict(self, odict: OrderedDict[str, StationObjectImage]):
        self._obj_dict = odict

    def handling_ap(self, ap: AttribValues, new_str_value: str, check_mode: bool, ad: AttributeErrorData):
        super().handling_ap(ap, new_str_value, check_mode, ad)
        if new_str_value and check_mode:
            if (not new_str_value) or new_str_value.isspace():
                raise AENameEmptyError("Name is empty", ad)
            if not new_str_value.isalnum():
                raise AENameNotIdentifierError("Name '{}' is not valid identifier".format(new_str_value), ad)
            if new_str_value in self.obj_dict:
                raise AENameRepeatingError("Name '{}' repeats in class '{}'".format(new_str_value,
                                                                                    self.contains_cls_name), ad)
            ap.confirmed_value = self.obj_dict[new_str_value]
            ap.str_confirmed_value = new_str_value

    def make_name_suggestion(self) -> str:
        i = 0
        while True:
            i += 1
            candid_name = "{}_{}".format(self.contains_cls_name.replace("SOI", ""), i)
            if candid_name not in self.obj_dict:
                break
        return candid_name


def str_values_logic(attr_value: Union[AttribValues, list[AttribValues]]) -> tuple[str, bool]:
    is_suggested = False
    last_imp_val = attr_value.last_input_value
    conf_val = attr_value.str_confirmed_value
    # sugg_val = attr_value.suggested_value
    if conf_val:
        return conf_val, is_suggested
    # elif sugg_val:
    #     is_suggested = True
    #     return sugg_val, is_suggested
    else:
        return last_imp_val, is_suggested


class StationObjectImage:

    def __init__(self):
        self.object_prop_struct: ObjectProperties = ObjectProperties()
        self.init_object_prop_struct()

    def init_object_prop_struct(self):
        obj_prop = self.object_prop_struct
        cls = self.__class__
        for attr_name in [key for key in cls.__dict__.keys() if not key.startswith("__")]:
            complex_attr = ComplexAttribProperties()
            descriptor: UniversalDescriptor = getattr(cls, attr_name)
            complex_attr.name = attr_name
            complex_attr.is_list = descriptor.is_list
            complex_attr.min_count = descriptor.min_count
            complex_attr.exactly_count = descriptor.exactly_count
            complex_attr.immutable = descriptor.immutable
            if complex_attr.min_count != -1:
                for index in range(complex_attr.min_count):
                    single_attr = SingleAttribProperties()
                    single_attr.index = index
                    complex_attr.single_attr_list.append(single_attr)
            if complex_attr.exactly_count != -1:
                for index in range(complex_attr.exactly_count):
                    single_attr = SingleAttribProperties()
                    single_attr.index = index
                    complex_attr.single_attr_list.append(single_attr)
            obj_prop.attrib_list.append(complex_attr)

    def get_complex_attr_prop(self, attr_name: str) -> ComplexAttribProperties:
        result_set = set()
        for complex_attr_prop_candidate in self.object_prop_struct.attrib_list:
            if complex_attr_prop_candidate.name == attr_name:
                result_set.add(complex_attr_prop_candidate)
        assert result_set, "Attr not found"
        assert len(result_set) < 2, "More then 1 found"
        return result_set.pop()

    def get_single_attr_prop(self, attr_name: str, index: int = -1) -> SingleAttribProperties:
        result_set = set()
        complex_attr_prop = self.get_complex_attr_prop(attr_name)
        for single_attr_prop_candidate in complex_attr_prop.single_attr_list:
            if single_attr_prop_candidate.index == index:
                result_set.add(single_attr_prop_candidate)
        assert result_set, "Attr not found"
        assert len(result_set) < 2, "More then 1 found"
        return result_set.pop()

        # all attrs initialization
        # for attr_name in self.active_attrs:
        #     descr: UniversalDescriptor = getattr(self.__class__, attr_name)
        #     if not descr.is_list:
        #         setattr(self, attr_name, ("", False))
        #     else:
        #         if descr.min_count != -1:
        #             for _ in range(descr.min_count):
        #                 setattr(self, attr_name, ("", False, IndexManagementCommand(command="append")))
        #         if descr.exactly_count != -1:
        #             for _ in range(descr.exactly_count):
        #                 setattr(self, attr_name, ("", False, IndexManagementCommand(command="append")))


    # def init_object_prop_struct(self) -> None:
    #     obj_prop = self.object_prop_struct
    #     obj_prop.name = self.name
    #     for attr_name in self.active_attrs:
    #         complex_attr = ComplexAttribProperties()
    #         complex_attr.name = attr_name
    #         attr_value: Union[AttribValues, list[AttribValues]] = getattr(self, attr_name)
    #         if isinstance(attr_value, list):
    #             complex_attr.is_list = True
    #             for i, attr_val in enumerate(attr_value):
    #                 single_attr = SingleAttribProperties()
    #                 single_attr.index = i
    #                 single_attr.str_value, single_attr.is_suggested = str_values_logic(attr_val)
    #                 complex_attr.single_attr_list.append(single_attr)
    #         else:
    #             single_attr = SingleAttribProperties()
    #             single_attr.str_value, single_attr.is_suggested = str_values_logic(attr_value)
    #             complex_attr.single_attr_list.append(single_attr)
    #         obj_prop.attrib_list.append(complex_attr)

    # def change_attrib_value(self, attr_name: str, attr_value: Union[str, list[str]], index: int = -1,
    #                         check_mode: bool = True):

        # set attr
        # if attr_name == "name":
        #     self.object_prop_struct.name = attr_value
        #     setattr(self, attr_name, attr_value)
        #     return
        # else:
        #     descr: UniversalDescriptor = getattr(self.__class__, attr_name)
        #     if not descr.is_list:
        #         assert isinstance(attr_value, str)
        #         setattr(self, attr_name, (attr_value, check_mode))
        #     elif index == -1:
        #         if isinstance(attr_value, str):
        #             attr_value = [attr_value]
        #         setattr(self, attr_name, (attr_value, check_mode, IndexManagementCommand(command="set_list")))
        #     else:
        #         setattr(self, attr_name, (attr_value, check_mode, IndexManagementCommand(command="set_index", index=index)))

        # switch attr
        # if (self.__class__ in SWITCH_ATTR_LISTS) and (attr_name in SWITCH_ATTR_LISTS[self.__class__]):
        #     chal: ChangeAttribList = SWITCH_ATTR_LISTS[self.__class__][attr_name]
        #     for remove_value in chal.remove_list(attr_value):
        #         if remove_value in self.active_attrs:
        #             self.active_attrs.remove(remove_value)
        #     index_insert = self.active_attrs.index(attr_name) + 1
        #     for add_value in reversed(chal.add_list(attr_value)):
        #         if add_value not in self.active_attrs:
        #             self.active_attrs.insert(index_insert, add_value)

    """ interface attribute setter """
    def change_single_attrib_value(self, attr_name: str, attr_value: Union[str, list[str]], index: int = -1,
                                   file_read_mode: bool = True):
        complex_attr = self.get_complex_attr_prop(attr_name)
        single_attr = self.get_single_attr_prop(attr_name, index)

        """ 1. New == old input """
        if attr_value == single_attr.last_input_str_value:
            return

        """ 2. Empty input """
        if attr_value == "":
            if single_attr.suggested_str_value:
                single_attr.interface_str_value = single_attr.suggested_str_value
                return
            if single_attr.is_required:
                return
            else:
                single_attr.error_message = ""
                return

        """ 3. File read input - delayed check """
        if not file_read_mode:
            assert not isinstance(attr_value, list)

        if file_read_mode:
            assert index == -1
            if isinstance(attr_value, list):
                assert getattr(self.__class__, attr_name).is_list
            complex_attr.temporary_value = attr_value
            return

        """ 4. Interactive input """
        single_attr.last_input_str_value = attr_value
        attr_value: str
        try:
            setattr(self, attr_name, attr_value)
        except AttributeEvaluateError as e:
            single_attr.error_message = form_message_from_error(e)
            self.object_prop_struct.creation_readiness = False
        else:
            single_attr.error_message = ""
            if attr_name == "name":
                self.object_prop_struct.name = attr_value
        finally:
            single_attr.interface_str_value = attr_value
            return

    @property
    def active_complex_attrs(self) -> list[ComplexAttribProperties]:
        return [self.get_complex_attr_prop(complex_attr_name) for complex_attr_name in self.object_prop_struct.active_attrs]

    def delayed_check(self):
        """ when attributes read from file, need to check after all names got """
        for complex_attr in self.active_complex_attrs:
            assert len(complex_attr.single_attr_list) == 1
            if complex_attr.is_list:
                """ now parsing here, not in file read """
                list_str_value = [s.strip() for s in complex_attr.temporary_value.split(" ") if s]
                setattr(self, complex_attr.name, (list_str_value,
                                                  IndexManagementCommand(command="set_list")))
            else:
                setattr(self, complex_attr.name, (complex_attr.temporary_value,
                                                  IndexManagementCommand(command="set_list", index=-1)))

    def change_object_refresh(self):
        """ when focus out, we need to reset all str_value-s of single attrs from failed to last_applied """
        for complex_attr in self.active_complex_attrs:
            for single_attr in complex_attr.single_attr_list:
                single_attr.interface_str_value = single_attr.last_applied_str_value

    def append_index_to_attrib(self, attr_name: str):
        complex_attr = self.get_complex_attr_prop(attr_name)

    def remove_index_from_attrib(self, attr_name: str, index: int):
        complex_attr = self.get_complex_attr_prop(attr_name)
        single_attr = self.get_single_attr_prop(attr_name, index)

    def suggest_attr_value(self, attr_name: str, attr_value: str, index: int = -1):
        single_attr = self.get_single_attr_prop(attr_name, index)
        single_attr.suggested_str_value = attr_value

    def apply_obj_creation(self):
        """ to store last_applied values """
        """ ! check auto-values not implemented """
        for complex_attr in self.active_complex_attrs:
            for single_attr in complex_attr.single_attr_list:
                single_attr.last_applied_str_value = single_attr.last_input_str_value

    # def default_switch_attrs(self):




    def reload_attr_value(self, attr_name: str):
        attr_prop_values = getattr(self, attr_name)
        if isinstance(attr_prop_values, AttribValues):
            self.change_single_attrib_value(attr_name, attr_prop_values.last_input_value)
        else:
            self.change_single_attrib_value(attr_name, self.list_attr_input_value(attr_name))

    """ interface list attribute input str getter """
    def list_attr_input_value(self, attr_name: str):
        attr_prop_values = getattr(self, attr_name)
        if isinstance(attr_prop_values, AttribValues):
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
        if isinstance(attr_prop_values, AttribValues):
            attr_prop_values = [attr_prop_values]
        return [apv.str_confirmed_value for apv in attr_prop_values]

    # """ interface list attribute str suggested value getter """
    # def list_attr_str_suggested_value(self, attr_name: str):
    #     attr_prop_values = getattr(self, attr_name)
    #     if isinstance(attr_prop_values, AttribValues):
    #         attr_prop_values = [attr_prop_values]
    #     return [apv.suggested_value for apv in attr_prop_values]

    """ interface list attribute confirmed value getter """
    def attr_confirmed_value(self, attr_name: str):
        attr_prop_values = getattr(self, attr_name)
        if isinstance(attr_prop_values, AttribValues):
            return attr_prop_values.confirmed_value
        else:
            return [attr_prop_value.confirmed_value for attr_prop_value in attr_prop_values]


class CoordinateSystemSOI(StationObjectImage):
    name = NameDescriptor("CoordinateSystemSOI")
    dependence = EnumDescriptor(CEDependence.possible_values)
    cs_relative_to = StationObjectDescriptor("CoordinateSystemSOI")
    x = IntDescriptor()
    co_x = EnumDescriptor(CEBool.possible_values)
    co_y = EnumDescriptor(CEBool.possible_values)


class AxisSOI(StationObjectImage):
    name = NameDescriptor("AxisSOI")
    cs_relative_to = StationObjectDescriptor("CoordinateSystemSOI")
    creation_method = EnumDescriptor(CEAxisCreationMethod.possible_values)
    y = IntDescriptor()
    center_point = StationObjectDescriptor("PointSOI")
    alpha = IntDescriptor()


class PointSOI(StationObjectImage):
    name = NameDescriptor("PointSOI")
    on = EnumDescriptor(CEAxisOrLine.possible_values)
    axis = StationObjectDescriptor("AxisSOI")
    line = StationObjectDescriptor("LineSOI")
    cs_relative_to = StationObjectDescriptor("CoordinateSystemSOI")
    x = PicketDescriptor()


class LineSOI(StationObjectImage):
    name = NameDescriptor("LineSOI")
    points = StationObjectDescriptor("PointSOI", is_list=True)


class LightSOI(StationObjectImage):
    name = NameDescriptor("LightSOI")
    light_route_type = EnumDescriptor(CELightRouteType.possible_values)
    center_point = StationObjectDescriptor("PointSOI")
    direct_point = StationObjectDescriptor("PointSOI")
    colors = EnumDescriptor(CELightColor.possible_values, is_list=True)
    light_stick_type = EnumDescriptor(CELightStickType.possible_values)


class RailPointSOI(StationObjectImage):
    name = NameDescriptor("RailPointSOI")
    center_point = StationObjectDescriptor("PointSOI")
    dir_plus_point = StationObjectDescriptor("PointSOI")
    dir_minus_point = StationObjectDescriptor("PointSOI")


class BorderSOI(StationObjectImage):
    name = NameDescriptor("BorderSOI")
    point = StationObjectDescriptor("PointSOI")
    border_type = EnumDescriptor(CEBorderType.possible_values)


class SectionSOI(StationObjectImage):
    name = NameDescriptor("SectionSOI")
    border_points = StationObjectDescriptor("PointSOI", is_list=True)


# SWITCH_ATTR_LISTS = {CoordinateSystemSOI: {"dependence": ChangeAttribList(OrderedDict({"independent": [],
#                                                                                        "dependent": [
#                                                                                            "cs_relative_to",
#                                                                                            "x",
#                                                                                            "co_x",
#                                                                                            "co_y"]}))},
#                      AxisSOI: {"creation_method": ChangeAttribList(OrderedDict({"rotational": [
#                          "center_point",
#                          "alpha"],
#                          "translational": ["y"]}))},
#                      PointSOI: {"on": ChangeAttribList(OrderedDict({"axis": ["axis"],
#                                                                     "line": ["line"]}))}
#                      }

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
