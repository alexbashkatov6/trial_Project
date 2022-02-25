from __future__ import annotations
from typing import Optional
from collections import OrderedDict

from command_supervisor import CommandSupervisor
from model_builder import ModelBuilder
from soi_dg_storage import StorageDG
from files_operations import read_station_config
from soi_objects import StationObjectImage, CoordinateSystemSOI, AxisSOI, PointSOI,\
    AttributeEvaluateError
from form_exception_message import form_message_from_error
from soi_metadata import ClassProperties, ObjectProperties, ComplexAttribProperties, SingleAttribProperties


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
        self.storage_dg: StorageDG = StorageDG()
        self.current_object: Optional[StationObjectImage] = None
        self.current_object_is_new = True

        """ external states """
        self.curr_obj_creation_readiness: bool = False
        self.object_attrib_dict = None
        self.cls_objects_dict = None

        """ external changes flags """
        self.changed_creation_readiness: bool = False
        self.changed_object_attrib_dict: bool = False
        self.changed_cls_objects_dict: bool = False

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
        pass

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
        self.current_object = self.storage_dg.soi_objects[cls_name][obj_name]
        self.current_object_is_new = False

    def delete_request(self, cls_name: str, obj_name: str):
        pass

    def delete_confirmed(self):
        pass

    def change_attribute_value(self, attr_name: str, new_value: str, index: int):
        """ interactive mode """
        new_value = new_value.strip()
        curr_obj = self.current_object
        object_prop_struct = curr_obj.object_prop_struct
        # complex_attr = curr_obj.get_complex_attr_prop(attr_name)
        single_attr = curr_obj.get_single_attr_prop(attr_name, index)

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

        """ 3. Input in general """
        try:
            setattr(curr_obj, attr_name, new_value)
        except AttributeEvaluateError as e:
            single_attr.error_message = form_message_from_error(e)
            self.check_changed_curr_obj_creation_readiness()
            return
        single_attr.error_message = ""
        if attr_name == "name":
            object_prop_struct.name = new_value
            return
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
        pass

    def remove_attrib_single_value(self, attr_name: str, index: int):
        pass

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
        object_prop_struct = curr_obj.object_prop_struct

        """ 1. Default build switches """
        for cls in SWITCH_ATTR_LISTS:
            change_list_dict = SWITCH_ATTR_LISTS[cls]
            new_attributes_reversed = []
            if isinstance(self.current_object, cls) and (attr_name in change_list_dict):
                change_attrib_list = change_list_dict[attr_name]
                for remove_value in change_attrib_list.remove_list(new_value):
                    if remove_value in object_prop_struct.active_attrs:
                        object_prop_struct.active_attrs.remove(remove_value)
                index_insert = object_prop_struct.active_attrs.index(attr_name) + 1
                for add_value in reversed(change_attrib_list.add_list(new_value)):
                    if add_value not in object_prop_struct.active_attrs:
                        new_attributes_reversed.append(add_value)
                        object_prop_struct.active_attrs.insert(index_insert, add_value)
                new_attributes = list(reversed(new_attributes_reversed))

    def model_rebuild_logic(self, attr_name: str, new_value: str, index: int):
        curr_obj = self.current_object
        cls_name = curr_obj.__class__.__name__
        obj_name = curr_obj.name
        dep_obj_names = self.storage_dg.dependent_objects_names(cls_name, obj_name)
        self.model_builder.rebuild_images(dep_obj_names)
