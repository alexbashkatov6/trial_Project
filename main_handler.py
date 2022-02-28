from __future__ import annotations
from typing import Optional, Callable
from collections import OrderedDict

from command_supervisor import CommandSupervisor
from model_builder import ModelBuilder
from soi_dg_storage import SOIDependenceGraph, SOIStorage
from files_operations import read_station_config
from soi_objects import StationObjectImage, CoordinateSystemSOI, AxisSOI, PointSOI,\
    AttributeEvaluateError, IndexManagementCommand
from form_exception_message import form_message_from_error
from soi_metadata import ClassProperties, ObjectProperties, ComplexAttribProperties, SingleAttribProperties
from attribute_object_key import ObjectKey, AttributeKey


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


class MainHandler:
    """ director """
    def __init__(self):
        self.cmd_sup: CommandSupervisor = CommandSupervisor()
        self.model_builder: ModelBuilder = ModelBuilder()
        self.storage: SOIStorage = SOIStorage()
        self.clean_storage_dg: SOIDependenceGraph = SOIDependenceGraph()
        self.dirty_storage_dg: SOIDependenceGraph = SOIDependenceGraph()
        self.current_object: Optional[StationObjectImage] = None
        self.current_object_is_new = True

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
        od_cls_objects = read_station_config(dir_name)
        self.clean_storage_dg.init_clean_nodes(od_cls_objects)
        soi_objects_no_gcs = self.clean_storage_dg.soi_objects_no_gcs
        for cls_name in soi_objects_no_gcs:
            for obj in soi_objects_no_gcs[cls_name].values():
                obj: StationObjectImage
                for complex_attr in obj.object_prop_struct.attrib_list:
                    if complex_attr.active:
                        attr_name = complex_attr.name
                        temp_val = complex_attr.temporary_value
                        if complex_attr.is_list:
                            elem_str_values = [val.strip() for val in temp_val.split(" ") if val]
                            for index, str_value in enumerate(elem_str_values):
                                self.append_attrib_single_value(attr_name)
                                self.change_attribute_value(attr_name, str_value, index)
                        else:
                            self.append_attrib_single_value(attr_name)
                            self.change_attribute_value(attr_name, temp_val)

    def dump_station_config(self, dir_name: str):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

    def eval_routes(self, dir_name: str):
        self.model_builder.eval_routes(dir_name)

    def create_new_object(self, cls_name: str):
        self.current_object: StationObjectImage = eval(cls_name)()
        self.current_object_is_new = True

    def change_current_object(self, cls_name: str, obj_name: str):
        curr_obj = self.current_object
        for complex_attr in curr_obj.active_complex_attrs:
            for single_attr in complex_attr.single_attr_list:
                single_attr.interface_str_value = single_attr.last_applied_str_value
        self.current_object = self.clean_storage_dg.soi_objects[cls_name][obj_name]
        self.current_object_is_new = False

    def delete_request(self, cls_name: str, obj_name: str):
        pass

    def delete_confirmed(self):
        pass

    def change_attribute_value(self, attr_name: str, new_value: str, index: int = -1):
        new_value = new_value.strip()
        curr_obj = self.current_object
        curr_obj_is_new = self.current_object_is_new
        cls = curr_obj.__class__
        cls_name = cls.__name__
        obj_name = curr_obj.name
        object_prop_struct = curr_obj.object_prop_struct
        complex_attr = curr_obj.get_complex_attr_prop(attr_name)
        single_attr = curr_obj.get_single_attr_prop(attr_name, index)
        old_applied_value = single_attr.last_applied_str_value
        old_input_value = single_attr.last_input_str_value  # for undo

        """ 1. New == old input """
        if new_value == single_attr.last_input_str_value:
            return

        single_attr.interface_str_value = new_value
        single_attr.is_suggested = False

        """ 2. Empty input """
        if new_value == "":
            if not single_attr.suggested_str_value:
                single_attr.suggested_str_value = self.suggestions_logic(attr_name, index)
            if single_attr.suggested_str_value:
                single_attr.interface_str_value = single_attr.suggested_str_value
                new_value = single_attr.suggested_str_value
                single_attr.is_suggested = True
            elif single_attr.is_required:
                single_attr.error_message = "Is required"
                self.check_changed_curr_obj_creation_readiness()
                return
            else:
                single_attr.error_message = ""
                self.check_changed_curr_obj_creation_readiness()
                return

        """ 3. Check input in general """
        try:
            if complex_attr.is_list:
                setattr(curr_obj, attr_name, (new_value, IndexManagementCommand(command="set_index", index=index)))
            else:
                setattr(curr_obj, attr_name, new_value)
        except AttributeEvaluateError as e:
            single_attr.error_message = form_message_from_error(e)
            self.check_changed_curr_obj_creation_readiness()
            return
        else:
            single_attr.error_message = ""

        """ 4. If change attr name, rename obj """
        if attr_name == "name":
            object_prop_struct.name = new_value

        """ 5. If success, make dg operations """
        if not curr_obj_is_new:
            if attr_name == "name":
                self.clean_storage_dg.rename_object(cls_name, old_applied_value, new_value)
                return
            else:
                self.clean_storage_dg.change_attrib_value_existing(cls_name, obj_name, attr_name, new_value, index)

        self.switch_logic(attr_name, new_value, index)
        self.check_changed_curr_obj_creation_readiness()

        if self.curr_obj_creation_readiness:
            self.model_rebuild_logic(attr_name, new_value, index)

    def apply_creation_new_object(self):
        curr_obj = self.current_object
        for complex_attr in curr_obj.active_complex_attrs:
            for single_attr in complex_attr.single_attr_list:
                single_attr.last_applied_str_value = single_attr.last_input_str_value

    def append_attrib_single_value(self, attr_name: str):
        self.current_object.append_complex_attr_index(attr_name)
        complex_attr = self.current_object.get_complex_attr_prop(attr_name)
        if complex_attr.is_list:
            self.change_attribute_value(attr_name, "", len(complex_attr.single_attr_list)-1)
        else:
            self.change_attribute_value(attr_name, "")

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

    def suggestions_logic(self, attr_name: str, index: int) -> Optional[str]:
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
                        single_attr.interface_str_value = single_attr.last_applied_str_value
                for activate_attr_name in change_attrib_list.add_list(new_value):
                    complex_attr_prop = curr_obj.get_complex_attr_prop(activate_attr_name)
                    complex_attr_prop.active = True
                    for single_attr in complex_attr_prop.single_attr_list:
                        self.change_attribute_value(complex_attr_prop.name, single_attr.interface_str_value, single_attr.index)

    def model_rebuild_logic(self, attr_name: str, new_value: str, index: int):
        curr_obj = self.current_object
        cls_name = curr_obj.__class__.__name__
        obj_name = curr_obj.name
        dep_obj_names = self.clean_storage_dg.dependent_objects_keys(cls_name, obj_name)
        self.model_builder.rebuild_images(dep_obj_names)


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
