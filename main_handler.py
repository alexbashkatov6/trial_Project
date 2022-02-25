from __future__ import annotations
from typing import Optional

from command_supervisor import CommandSupervisor
from model_builder import ModelBuilder
from soi_dg_storage import StorageDG
from files_operations import read_station_config
from soi_objects import StationObjectImage


class MainHandler:
    """ director """
    def __init__(self):
        self.cmd_sup: CommandSupervisor = CommandSupervisor()
        self.mod_bld: ModelBuilder = ModelBuilder()
        self.stg_dg: StorageDG = StorageDG()
        self.current_object: Optional[StationObjectImage] = None

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
        pass

    def create_new_object(self, cls_name: str):
        pass

    def change_current_object(self, cls_name: str, obj_name: str):
        pass

    def delete_request(self, cls_name: str, obj_name: str):
        pass

    def delete_confirmed(self):
        pass

    def change_attribute_value(self, attr_name: str, new_value: str, index: int):
        """ interactive mode """
        new_value = new_value.strip()
        curr_obj = self.current_object
        object_prop_struct = curr_obj.object_prop_struct
        complex_attr = curr_obj.get_complex_attr_prop(attr_name)
        single_attr = curr_obj.get_single_attr_prop(attr_name, index)

        """ 1. New == old input """
        if new_value == single_attr.last_input_str_value:
            return

        """ 2. Empty input """
        if new_value == "":
            if single_attr.suggested_str_value:
                single_attr.interface_str_value = single_attr.suggested_str_value
                return
            else:
                """ not implemented yet """
                pass

    def apply_creation_new_object(self):
        pass

    def append_attrib_single_value(self, attr_name: str):
        pass

    def remove_attrib_single_value(self, attr_name: str, index: int):
        pass
