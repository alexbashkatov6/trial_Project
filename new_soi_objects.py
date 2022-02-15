from __future__ import annotations
from typing import Type, Union, Iterable
from collections import OrderedDict
from copy import copy
from dataclasses import dataclass

from custom_enum import CustomEnum
from enums_images import CEDependence, CEBool, CEAxisCreationMethod, CEAxisOrLine, CELightRouteType, CELightStickType, \
    CEBorderType, CELightColor
from picket_coordinate import PicketCoordinate
from default_ordered_dict import DefaultOrderedDict
# from attrib_properties import AttribProperties
# from attrib_index import CompositeAttributeIndex

from config_names import GLOBAL_CS_NAME


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
    # last_confirmed_value: str = ""
    # suggested_value: str = ""
    #
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

    def __set__(self, instance, value: Union[str, tuple[str, IndexManagementCommand]]):

        ap_for_handle_list = []
        # print("got value = ", value, type(value))
        if not self.is_list:
            assert isinstance(value, str)
            str_value = value
            if not hasattr(instance, "_{}".format(self.name)):
                ap_for_handle = AttribProperties()
                setattr(instance, "_{}".format(self.name), ap_for_handle)
            else:
                ap_for_handle = getattr(instance, "_{}".format(self.name))
            self.handling_ap(ap_for_handle, str_value)
        else:
            assert isinstance(value, tuple)
            command = value[1].command
            index = value[1].index

            if not hasattr(instance, "_{}".format(self.name)):
                setattr(instance, "_{}".format(self.name), [])
            old_ap_list: list[AttribProperties] = getattr(instance, "_{}".format(self.name))
            if command in ["remove_index", "append", "set_index"]:
                str_value = value[0]
                if command == "remove_index":
                    old_ap_list.pop(index)
                    return
                if command == "append":
                    ap_for_handle = AttribProperties()
                    old_ap_list.append(ap_for_handle)
                if command == "set_index":
                    ap_for_handle = old_ap_list[index]
                self.handling_ap(ap_for_handle, str_value)
            elif command == "set_list":
                old_ap_list.clear()
                str_list = value[0]
                for str_value in str_list:
                    ap_for_handle = AttribProperties()
                    self.handling_ap(ap_for_handle, str_value)
                    old_ap_list.append(ap_for_handle)

        for ap_for_handle_ in ap_for_handle_list:
            self.handling_ap(ap_for_handle_, str_value)

    def handling_ap(self, ap: AttribProperties, new_str_value: str):
        ap.last_input_value = new_str_value


class BoundedStrSetDescriptor(UniversalDescriptor):

    def __init__(self, possible_values: list[str] = None, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count)
        if not possible_values:
            self._possible_values = []
        else:
            self._possible_values = possible_values

    @property
    def possible_values(self) -> list[str]:
        result = list(self._possible_values)
        return result

    @possible_values.setter
    def possible_values(self, values: Iterable[str]):
        self._possible_values = values

    def handling_ap(self, ap: AttribProperties, new_str_value: str):
        super().handling_ap(ap, new_str_value)
        if self.possible_values:
            if new_str_value and (new_str_value not in self.possible_values):
                raise ValueError("Value {} not in possible list: {}".format(new_str_value, self.possible_values))
            # print("POSSIBLE VALUES DEFINED")


class IntDescriptor(UniversalDescriptor):

    def __init__(self, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count)

    def handling_ap(self, ap: AttribProperties, new_str_value: str):
        super().handling_ap(ap, new_str_value)
        if new_str_value:
            int(new_str_value)


class PicketDescriptor(UniversalDescriptor):

    def __init__(self, *, is_required: bool = True, is_list: bool = False,
                 min_count: int = -1, exactly_count: int = -1):
        super().__init__(is_required=is_required, is_list=is_list, min_count=min_count, exactly_count=exactly_count)

    def handling_ap(self, ap: AttribProperties, new_str_value: str):
        super().handling_ap(ap, new_str_value)
        if new_str_value:
            PicketCoordinate(new_str_value)


class StationObjectImage:
    name = SOIName()

    def __init__(self):
        self.active_attrs = [attr_name for attr_name in self.__class__.__dict__ if not attr_name.startswith("__")]
        self.switch_attr_lists = {CoordinateSystemSOI: {"dependence": ChangeAttribList(OrderedDict({"independent": [],
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
        # all attrs initialization
        for attr_name in self.active_attrs:
            descr: UniversalDescriptor = getattr(self.__class__, attr_name)
            if not descr.is_list:
                setattr(self, attr_name, "")
            else:
                if descr.min_count != -1:
                    for _ in range(descr.min_count):
                        setattr(self, attr_name, ("", IndexManagementCommand(command="append")))
                if descr.exactly_count != -1:
                    for _ in range(descr.exactly_count):
                        setattr(self, attr_name, ("", IndexManagementCommand(command="append")))

        # switch attrs initialization
        if self.__class__ in self.switch_attr_lists:
            for attr_name in self.switch_attr_lists[self.__class__]:
                chal: ChangeAttribList = self.switch_attr_lists[self.__class__][attr_name]
                # print("preferred_value", chal.preferred_value)
                self.changed_attrib_value(attr_name, chal.preferred_value)

    def changed_attrib_value(self, attr_name: str, attr_value: Union[str, list[str]]):

        # set attr
        if attr_name == "name":
            setattr(self, attr_name, attr_value)
            return
        else:
            descr: UniversalDescriptor = getattr(self.__class__, attr_name)
            if not descr.is_list:
                assert isinstance(attr_value, str)
                setattr(self, attr_name, attr_value)
            else:
                assert isinstance(attr_value, list)
                setattr(self, attr_name, (attr_value, IndexManagementCommand(command="set_list")))

        # switch attr
        if (self.__class__ in self.switch_attr_lists) and (attr_name in self.switch_attr_lists[self.__class__]):
            chal: ChangeAttribList = self.switch_attr_lists[self.__class__][attr_name]
            for remove_value in chal.remove_list(attr_value):
                if remove_value in self.active_attrs:
                    self.active_attrs.remove(remove_value)
            index_insert = self.active_attrs.index(attr_name) + 1
            for add_value in reversed(chal.add_list(attr_value)):
                if add_value not in self.active_attrs:
                    self.active_attrs.insert(index_insert, add_value)


class CoordinateSystemSOI(StationObjectImage):
    dependence = BoundedStrSetDescriptor(CEDependence.possible_values)
    cs_relative_to = BoundedStrSetDescriptor()
    x = IntDescriptor()
    co_x = BoundedStrSetDescriptor(CEBool.possible_values)
    co_y = BoundedStrSetDescriptor(CEBool.possible_values)


class AxisSOI(StationObjectImage):
    cs_relative_to = BoundedStrSetDescriptor()
    creation_method = BoundedStrSetDescriptor(CEAxisCreationMethod.possible_values)
    y = IntDescriptor()
    center_point = BoundedStrSetDescriptor()
    alpha = BoundedStrSetDescriptor()


class PointSOI(StationObjectImage):
    on = BoundedStrSetDescriptor(CEAxisOrLine.possible_values)
    axis = BoundedStrSetDescriptor()
    line = BoundedStrSetDescriptor()
    cs_relative_to = BoundedStrSetDescriptor()
    x = PicketDescriptor()


class LineSOI(StationObjectImage):
    points = BoundedStrSetDescriptor(is_list=True)


class LightSOI(StationObjectImage):
    light_route_type = BoundedStrSetDescriptor(CELightRouteType.possible_values)
    center_point = BoundedStrSetDescriptor()
    direct_point = BoundedStrSetDescriptor()
    colors = BoundedStrSetDescriptor(CELightColor.possible_values, is_list=True)
    light_stick_type = BoundedStrSetDescriptor(CELightStickType.possible_values)


class RailPointSOI(StationObjectImage):
    center_point = BoundedStrSetDescriptor()
    dir_plus_point = BoundedStrSetDescriptor()
    dir_minus_point = BoundedStrSetDescriptor()


class BorderSOI(StationObjectImage):
    point = BoundedStrSetDescriptor()
    border_type = BoundedStrSetDescriptor(CEBorderType.possible_values)


class SectionSOI(StationObjectImage):
    border_points = BoundedStrSetDescriptor(is_list=True)


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
        cs.changed_attrib_value("dependence", "dependent")
        print(cs.active_attrs)
        cs.changed_attrib_value("dependence", "independent")
        print(cs.active_attrs)
        cs.changed_attrib_value("dependence", "dependent")
        print(cs.active_attrs)
        print("attr_values", [(active_attr, getattr(cs, active_attr)) for active_attr in cs.active_attrs])

        cs = AxisSOI()
        # cs.creation_method
        print(cs.active_attrs)
        cs.changed_attrib_value("creation_method", "translational")
        print(cs.active_attrs)
        cs.changed_attrib_value("creation_method", "rotational")
        print(cs.active_attrs)
        cs.changed_attrib_value("creation_method", "translational")
        print(cs.active_attrs)

        cs = PointSOI()
        # cs.creation_method
        print(cs.active_attrs)
        cs.changed_attrib_value("on", "axis")
        print(cs.active_attrs)
        cs.changed_attrib_value("on", "line")
        print(cs.active_attrs)
        cs.changed_attrib_value("on", "axis")
        print(cs.active_attrs)

        cs = BorderSOI()
        # cs.creation_method
        print(cs.active_attrs)