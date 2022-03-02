from __future__ import annotations
from typing import Optional, Callable
from collections import OrderedDict

from model_builder import ModelBuilder
from soi_dg_storage import SOIDependenceGraph, SOIStorage, DependenciesBuildError
from files_operations import read_station_config
from soi_objects import StationObjectImage, CoordinateSystemSOI, AxisSOI, PointSOI, LineSOI, LightSOI, \
    RailPointSOI, BorderSOI, SectionSOI, AttributeEvaluateError, IndexManagementCommand, StationObjectDescriptor
from form_exception_message import form_message_from_error
from soi_metadata import ClassProperties, ObjectProperties, ComplexAttribProperties, SingleAttribProperties
from attribute_object_key import ObjectKey, AttributeKey
from default_ordered_dict import DefaultOrderedDict


def form_message_from_error(e: Exception):
    print("ERROR", e.args)


class ExecuteFunctionProperties:
    def __init__(self, _method: Callable, *args):
        self._method = _method
        self.args = args

    def execute(self):
        self._method(*self.args)


class ChangeAttribList:
    def __init__(self, attr_value_add_dict: OrderedDict[str, list[str]]):
        self.attr_value_add_dict = attr_value_add_dict

    def add_list(self, attr_value) -> list[str]:
        return self.attr_value_add_dict[attr_value]

    def remove_list(self, attr_value) -> list[str]:
        result = []
        for attr_val in self.attr_value_add_dict:
            if attr_val != attr_value:
                result.extend(self.attr_value_add_dict[attr_val])
        return result


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


def soi_to_obj_keys(soi_dict: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]]) -> \
        list[ObjectKey]:
    result = []
    for cls_name in soi_dict:
        for obj_name in soi_dict[cls_name]:
            result.append(ObjectKey(cls_name, obj_name))
    return result


class MainHandler:
    """ director """
    def __init__(self):
        self.model_builder: ModelBuilder = ModelBuilder()
        self.soi_storage: SOIStorage = SOIStorage()
        self.dependence_graph: SOIDependenceGraph = SOIDependenceGraph()
        self.current_object: Optional[StationObjectImage] = None
        self.current_object_is_new = True
        self.safety_apply_mode = True

        """ external states """
        self.cls_objects_dict: OrderedDict = OrderedDict()
        self.current_object_attrib_dict: OrderedDict = OrderedDict()
        self.curr_obj_creation_readiness: bool = False

        """ external changes flags """
        self.changed_cls_objects_dict: bool = False
        self.changed_current_object_attrib_dict: bool = False
        self.changed_creation_readiness: bool = False

    """ 
        Interface input commands:
    1. Menu commands
        1.1 'File' menu commands 
            - read_station_config
            - dump_station_config
        1.2 'Edit' menu commands
            - undo
            - redo
        1.3 'Evaluations' menu commands
            - eval_routes
    2. Create toolbar commands
        - create_new_object
    3. Tree object toolbar commands
        - change_current_object
        - delete_request
    4. Delete warning menu command
        - delete_confirmed
    5. Attributes toolbar commands
        - change_attribute_value
        - apply_creation_new_object
        - append_attrib_single_value
        - remove_attrib_single_value
    """

    def read_station_config(self, dir_name: str):
        # self.safety_apply_mode = False
        od_cls_objects = read_station_config(dir_name)
        for cls_name in od_cls_objects:
            print("cls_name", cls_name)
            for obj_name, obj in od_cls_objects[cls_name].items():
                print("obj", obj)
                self.create_new_object(cls_name)
                for complex_attr in obj.object_prop_struct.attrib_list:
                    print("complex_attr", complex_attr)
                    if complex_attr.active:
                        attr_name = complex_attr.name
                        print("attr_name", attr_name)
                        temp_val = complex_attr.temporary_value
                        if complex_attr.is_list:
                            elem_str_values = [val.strip() for val in temp_val.split(" ") if val]
                            for index, str_value in enumerate(elem_str_values):
                                self.append_attrib_single_value(attr_name)
                                self.change_attribute_value(attr_name, str_value, index)
                        else:
                            self.change_attribute_value(attr_name, temp_val)
                self.apply_creation_new_object()

    def dump_station_config(self, dir_name: str):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

    def eval_routes(self, dir_name: str):
        self.model_builder.eval_routes(dir_name)

    def create_new_object(self, cls_name: str):
        self.current_object: StationObjectImage = eval(cls_name+"SOI")()
        self.current_object_is_new = True
        self.current_object.name = self.suggestions_logic("name")
        self.current_object.get_single_attr_prop("name").last_input_str_value = self.current_object.name
        self.dependence_graph.add_obj_node_dg(ObjectKey(cls_name, self.current_object.name))
        self.soi_storage.add_single_obj_to_soi(cls_name, self.current_object.name, self.current_object)

    def change_current_object(self, cls_name: str, obj_name: str):
        curr_obj = self.current_object
        for complex_attr in curr_obj.active_complex_attrs:
            for single_attr in complex_attr.single_attr_list:
                single_attr.interface_str_value = single_attr.last_confirmed_str_value
        self.current_object = self.dependence_graph.soi_objects[cls_name][obj_name]
        self.current_object_is_new = False

    def delete_request(self, cls_name: str, obj_name: str):
        pass

    def delete_confirmed(self):
        pass

    def change_attribute_value(self, attr_name: str, new_value: str, index: int = -1):
        new_value = new_value.strip()
        if not self.current_object_is_new:
            self.safety_apply_mode = False
        self.change_attribute_value_logic(attr_name, new_value, index)

    def common_attrib_check(self, cls_name: str, obj_name: str, attr_name: str, new_value: str, index: int = -1,
                            recheck_old_value: bool = False):
        print("common_attrib_check, cls_name={}, obj_name={}, attr_name={}, new_value={}, index={}, recheck_old_value={}"
              .format(cls_name, obj_name, attr_name, new_value, index, recheck_old_value))
        obj: StationObjectImage = self.soi_storage.soi_objects[cls_name][obj_name]
        cls = obj.__class__
        cls_name = cls_name.replace("SOI", "")
        descriptor = getattr(cls, attr_name)
        object_prop_struct = obj.object_prop_struct
        complex_attr = obj.get_complex_attr_prop(attr_name)
        single_attr = obj.get_single_attr_prop(attr_name, index)
        old_value = single_attr.last_input_str_value

        """ 1. New == old input """
        if (not recheck_old_value) and (new_value == single_attr.last_input_str_value):
            return

        single_attr.last_input_str_value = new_value
        single_attr.interface_str_value = new_value
        single_attr.is_suggested = False

        """ 2. Empty input """
        """ maybe new_value can be suggested """
        if new_value == "":
            if not single_attr.suggested_str_value:
                single_attr.suggested_str_value = self.suggestions_logic(attr_name, index)
            if single_attr.suggested_str_value:
                single_attr.interface_str_value = single_attr.suggested_str_value
                new_value = single_attr.suggested_str_value
                single_attr.is_suggested = True
            elif single_attr.is_required:
                single_attr.error_message = "Is required"
                return
            else:
                single_attr.error_message = ""
                return

        """ 3. Check input in general """
        try:
            if complex_attr.is_list:
                setattr(obj, attr_name, (new_value, IndexManagementCommand(command="set_index", index=index)))
            else:
                setattr(obj, attr_name, new_value)
        except AttributeEvaluateError as e:
            """ 1. FORMAL ERRORS """
            single_attr.error_message = form_message_from_error(e)
            return
        else:
            """ 2. NO FORMAL ERRORS """
            single_attr.last_confirmed_str_value = new_value
            single_attr.error_message = ""

            """ 2.1. RENAME OPERATIONS """
            if attr_name == "name":
                """ rename in object_prop_struct """
                object_prop_struct.name = new_value
                """ rename in storage """
                self.soi_storage.rename_obj(cls_name, old_value, new_value)
                """ rename in dependence graph """
                old_attr_keys = self.dependence_graph.replace_obj_key(ObjectKey(cls_name, old_value),
                                                                      ObjectKey(cls_name, new_value))
                """ new value of dependent attributes """
                for old_attr_key in old_attr_keys:
                    self.common_attrib_check(old_attr_key.cls_name, old_attr_key.obj_name, old_attr_key.attr_name,
                                             new_value, old_attr_key.index)
                return

            """ 2.2. REBUILD DEPENDENCIES """
            if complex_attr.is_object:
                contains_cls_name = descriptor.contains_cls_name
                ak = AttributeKey(cls_name, obj_name, attr_name, index)
                if self.dependence_graph.check_dependence_existing(ak):
                    parent_obj_key, child_obj_key = self.dependence_graph.remove_dependence(ak)  # for rollback
                try:
                    self.dependence_graph.make_dependence(ObjectKey(contains_cls_name, new_value),
                                                          ObjectKey(cls_name, obj_name), ak, not self.safety_apply_mode)
                except DependenciesBuildError as e:
                    single_attr.error_message = form_message_from_error(e)

            """ 2.3. SWITCH OPERATIONS """
            self.switch_logic(attr_name, new_value, index)

    def change_attribute_value_logic(self, attr_name: str, new_value: str, index: int = -1):
        print("change_attribute_value_logic", self.safety_apply_mode)
        curr_obj = self.current_object
        cls = curr_obj.__class__
        cls_name = cls.__name__.replace("SOI", "")
        obj_name = curr_obj.name
        descriptor = getattr(cls, attr_name)
        object_prop_struct = curr_obj.object_prop_struct
        complex_attr = curr_obj.get_complex_attr_prop(attr_name)
        single_attr = curr_obj.get_single_attr_prop(attr_name, index)
        old_applied_value = single_attr.last_confirmed_str_value
        old_input_value = single_attr.last_input_str_value  # for undo

        self.common_attrib_check(cls_name, obj_name, attr_name, new_value, index)

        """ check other objects, if change name """
        if attr_name == "name":
            if not self.safety_apply_mode:
                print("Reset dg storages")
                self.dependence_graph.reset_storages()
                for cls_name_ in self.soi_storage.soi_objects_no_gcs:
                    for obj_name_ in self.soi_storage.soi_objects_no_gcs[cls_name_]:
                        obj: StationObjectImage = self.soi_storage.soi_objects_no_gcs[cls_name_][obj_name_]
                        if obj is self.current_object:
                            continue
                        for active_complex_attr in obj.active_complex_attrs:
                            if active_complex_attr.name == "name":
                                continue
                            attr_name_ = active_complex_attr.name
                            for single_attr_ in active_complex_attr.single_attr_list:
                                new_value_ = single_attr_.last_input_str_value
                                index_ = single_attr_.index
                                self.common_attrib_check(cls_name_, obj_name_, attr_name_, new_value_, index_, True)

    def check_apply_readiness(self) -> bool:
        curr_obj = self.current_object
        complex_name_attr = curr_obj.get_complex_attr_prop("name")
        single_name_attr = complex_name_attr.single_attr_list[0]
        if single_name_attr.error_message:
            return False
        return True

    def apply_creation_new_object(self):
        curr_obj = self.current_object
        for cls_name_ in self.soi_storage.soi_objects_no_gcs:
            for obj_name_ in self.soi_storage.soi_objects_no_gcs[cls_name_]:
                obj: StationObjectImage = self.soi_storage.soi_objects_no_gcs[cls_name_][obj_name_]
                for active_complex_attr in obj.active_complex_attrs:
                    for single_attr_ in active_complex_attr.single_attr_list:
                        if single_attr_.error_message:
                            self.safety_apply_mode = False
                            print("Apply safety_apply_mode = False")
                            return
        self.safety_apply_mode = True
        print("Apply safety_apply_mode = True")

    def append_attrib_single_value(self, attr_name: str):
        self.current_object.append_complex_attr_index(attr_name)
        complex_attr = self.current_object.get_complex_attr_prop(attr_name)
        if complex_attr.is_list:
            self.change_attribute_value_logic(attr_name, "", len(complex_attr.single_attr_list) - 1)
        else:
            self.change_attribute_value_logic(attr_name, "")

    def remove_attrib_single_value(self, attr_name: str, index: int):
        self.current_object.remove_complex_attr_index(attr_name, index)
        self.current_object.remove_descriptor_index(attr_name, index)

    """ Internal logic """

    def check_changed_curr_obj_creation_readiness(self):
        curr_obj = self.current_object
        creation_readiness_before = self.curr_obj_creation_readiness
        creation_readiness_after = True
        for active_attr in curr_obj.active_complex_attrs:
            for single_attr in active_attr.single_attr_list:
                if single_attr.error_message:
                    creation_readiness_after = False
                    break
            if not creation_readiness_after:
                break
        self.changed_creation_readiness = (creation_readiness_before != creation_readiness_after)

    def suggestions_logic(self, attr_name: str, index: int = -1) -> Optional[str]:
        curr_obj = self.current_object
        cls = curr_obj.__class__
        if attr_name == "name":
            descriptor = getattr(cls, attr_name)
            return descriptor.make_name_suggestion()

    def switch_logic(self, attr_name: str, new_value: str, index: int):
        """ switch_logic """
        curr_obj = self.current_object
        # object_prop_struct = curr_obj.object_prop_struct

        """ 1. Default build switches handling """
        for cls in SWITCH_ATTR_LISTS:
            change_list_dict = SWITCH_ATTR_LISTS[cls]
            if isinstance(self.current_object, cls) and (attr_name in change_list_dict):
                change_attrib_list = change_list_dict[attr_name]
                for deactivate_attr_name in change_attrib_list.remove_list(new_value):
                    complex_attr_prop = curr_obj.get_complex_attr_prop(deactivate_attr_name)
                    complex_attr_prop.active = False
                    """ single attr values rollback """
                    for single_attr in complex_attr_prop.single_attr_list:
                        single_attr.interface_str_value = single_attr.last_confirmed_str_value
                for activate_attr_name in change_attrib_list.add_list(new_value):
                    complex_attr_prop = curr_obj.get_complex_attr_prop(activate_attr_name)
                    complex_attr_prop.active = True
                    for single_attr in complex_attr_prop.single_attr_list:
                        self.change_attribute_value_logic(complex_attr_prop.name, single_attr.interface_str_value, single_attr.index)

    def model_rebuild_logic(self, attr_name: str, new_value: str, index: int):
        pass
        # curr_obj = self.current_object
        # cls_name = curr_obj.__class__.__name__
        # obj_name = curr_obj.name
        # dep_obj_names = self.dependence_graph.dependent_objects_keys(cls_name, obj_name)
        # self.model_builder.rebuild_images(dep_obj_names)


if __name__ == "__main__":

    test_1 = False
    if test_1:
        def my_func(x, y):
            print(x, y)

        efp = ExecuteFunctionProperties(my_func, 2, 3)
        efp.execute()

    test_2 = False
    if test_2:
        class A:
            def my_func(self, x, y):
                print(x, y)
        a = A()
        efp = ExecuteFunctionProperties(A.my_func, a, 2, 3)
        efp.execute()

    test_3 = True
    if test_3:
        mh = MainHandler()
        mh.read_station_config("station_in_config")
        print(len(mh.dependence_graph.dg.links))
