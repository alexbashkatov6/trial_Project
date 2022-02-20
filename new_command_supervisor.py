from __future__ import annotations
from collections import OrderedDict
import os
import pandas as pd
from typing import Optional

from custom_enum import CustomEnum
from new_soi_rectifier import StorageDG, DependenciesBuildError
from new_model_builder import ModelBuilder, ModelBuildError
from new_soi_objects import StationObjectImage
from extended_itertools import single_element
from soi_files_handler import read_station_config

from config_names import STATION_IN_CONFIG_FOLDER, GLOBAL_CS_NAME


class AttributeSoiError(Exception):
    pass


class ObjectSoiError(Exception):
    pass


class CECommand(CustomEnum):
    load_from_file = 0
    create_new_object = 1
    apply_creation_new_object = 2
    change_current_object = 3
    change_attrib_value = 4
    delete_obj = 5


class Command:
    def __init__(self, cmd_type: CECommand, cmd_args: list):
        self.cmd_type = cmd_type
        self.cmd_args = cmd_args


class CommandChain:
    def __init__(self):
        self.commands = []
        self.forward_args = []
        self.backward_args = []

    def append_command(self, command: Command):
        self.commands.append(command)

    def cut_slice(self, command: Command):
        """ command included in list"""
        self.commands = self.commands[:self.commands.index(command) + 1]

    def index_command_in_chain(self, command: Command) -> int:
        if command not in self.commands:
            return -1
        return self.commands.index(command)


class CommandSupervisor:
    def __init__(self):
        # commands state
        self.commands: list[Command] = []
        self.backward_args = []
        self.command_index = -1

        # functional classes
        self.storage = StorageDG()
        self.model = ModelBuilder()

        # current state variables
        self.objs_dict_changed = False
        self.apply_readiness = False

        # delete state variables
        self.deletion_names = []
        self.delete_request_name: Optional[tuple[str, str]] = None

    # def reset_storages(self):
    #     self.storage.reset_clean_storages()
    #     self.model.reset_storages()

    def model_building(self, images: list[StationObjectImage]):
        self.model.init_soi_list(images)
        self.model.build_skeleton()
        self.model.eval_link_length()
        self.model.build_lights()
        self.model.build_rail_points()
        self.model.build_borders()
        self.model.build_sections()

    def execute_command_at_pointer(self):
        command = self.commands[self.command_index]

        if command.cmd_type == CECommand.load_from_file:
            dir_name = command.cmd_args[0]
            new_objects = read_station_config(dir_name)
            # self.objs_dict_changed = True
            reset_objects = self.storage.reload_from_dict(new_objects)
            backward_arg = [reset_objects]

        if command.cmd_type == CECommand.create_new_object:
            cls_name = command.cmd_args[0]
            old_obj_params = self.storage.create_empty_new_object(cls_name)
            old_cls_name, old_obj_name = old_obj_params
            backward_arg = [old_cls_name, old_obj_name]

        if command.cmd_type == CECommand.change_current_object:
            cls_name = command.cmd_args[0]
            obj_name = command.cmd_args[1]
            old_obj_params = self.storage.select_current_object(cls_name, obj_name)
            old_cls_name, old_obj_name = old_obj_params
            backward_arg = [old_cls_name, old_obj_name]

        if command.cmd_type == CECommand.apply_creation_new_object:
            cls_name, obj_name = self.storage.apply_creation_current_object()
            backward_arg = [cls_name, obj_name]

        if command.cmd_type == CECommand.delete_obj:
            cls_name = command.cmd_args[0]
            obj_name = command.cmd_args[1]
            recover_obj_dict = self.storage.delete_object(cls_name, obj_name)
            backward_arg = [recover_obj_dict]

        if command.cmd_type == CECommand.change_attrib_value:
            attr_name = command.cmd_args[0]
            new_value = command.cmd_args[1]
            index = command.cmd_args[2]
            old_value = self.storage.change_attrib_value_main(attr_name, new_value, index)
            backward_arg = [attr_name, old_value, index]

        assert len(self.backward_args) >= self.command_index
        if len(self.backward_args) == self.command_index:
            self.backward_args.append(backward_arg)
        else:
            self.backward_args[self.command_index] = backward_arg

    def try_execute_command(self):
        try:
            self.execute_command_at_pointer()
        except AttributeSoiError:
            print("ERROR")
        else:
            self.model_building(self.storage.rectify_dg())

    def continue_commands(self, command: Command):
        cur_len = len(self.commands)
        for i in reversed(range(self.command_index+1, cur_len)):
            self.commands.pop(i)
        self.commands.append(command)
        self.command_index = len(self.commands)-1

    def undo(self):
        if self.command_index == -1:
            print("CANNOT UNDO")
            return
        command = self.commands[self.command_index]
        back_args = self.backward_args[self.command_index]
        if command.cmd_type == CECommand.load_from_file:
            self.storage.reload_from_dict(*back_args)
        if command.cmd_type == CECommand.create_new_object:
            self.storage.select_current_object(*back_args)
        if command.cmd_type == CECommand.change_current_object:
            self.storage.select_current_object(*back_args)
        if command.cmd_type == CECommand.apply_creation_new_object:
            self.storage.delete_object(*back_args)
        if command.cmd_type == CECommand.delete_obj:
            self.storage.recover_objects(*back_args)
        if command.cmd_type == CECommand.change_attrib_value:
            self.storage.change_attrib_value_main(*back_args)
        self.command_index -= 1

    def redo(self):
        if self.command_index == len(self.commands)-1:
            print("CANNOT REDO")
            return
        self.command_index += 1
        self.execute_command_at_pointer()

    def error_handler(self, cls_name: str, obj_name: str, attr_name: str, attr_index: int, message: str):
        if cls_name.endswith("SOI"):
            cls_name = cls_name.replace("SOI", "")
        print("Attribute error! \ncls_name: {} \nobj_name: {} \nattr_name: {} \nattr_index: {}\n message: {}"
              .format(cls_name, obj_name, attr_name, attr_index, message))

    """ High-level interface operations - by 'buttons' """

    def read_station_config(self, dir_name: str):
        self.continue_commands(Command(CECommand(CECommand.load_from_file), [dir_name]))
        self.try_execute_command()

    def create_new_object(self, cls_name: str):
        self.continue_commands(Command(CECommand(CECommand.create_new_object), [cls_name]))
        self.try_execute_command()

    def change_current_object(self, cls_name: str, obj_name: str):
        self.continue_commands(Command(CECommand(CECommand.change_current_object), [cls_name, obj_name]))
        self.try_execute_command()

    def change_attribute_value(self, attr_name: str, new_value: str, index: int):
        self.continue_commands(Command(CECommand(CECommand.change_attrib_value), [attr_name, new_value, index]))
        self.try_execute_command()

    def apply_creation_new_object(self):
        self.continue_commands(Command(CECommand(CECommand.apply_creation_new_object), []))
        self.try_execute_command()

    def delete_request(self, cls_name: str, obj_name: str):
        self.delete_request_name = (cls_name, obj_name)
        self.deletion_names = self.storage.dependent_objects_names(cls_name, obj_name)

    def delete_confirmed(self):
        cls_name, obj_name = self.delete_request_name
        print("deleted:", self.deletion_names)
        self.delete_request_name = None
        self.deletion_names = []
        self.continue_commands(Command(CECommand(CECommand.delete_obj), [cls_name, obj_name]))
        self.try_execute_command()

    def eval_routes(self, dir_name: str):
        self.model.eval_routes(dir_name)


if __name__ == "__main__":

    test_18 = False
    if test_18:
        cmd_sup = CommandSupervisor()
        cmd_sup.read_station_config(STATION_IN_CONFIG_FOLDER)
        obj_list = cmd_sup.storage.rectify_dg()
        cmd_sup.model_building(obj_list)
        cmd_sup.eval_routes("TrainRoute.xml", "ShuntingRoute.xml")

    test_19 = False
    if test_19:
        cmd_sup = CommandSupervisor()

        cmd_sup.read_station_config(STATION_IN_CONFIG_FOLDER)
        print(cmd_sup.storage.current_object)

        cmd_sup.change_current_object("CoordinateSystemSOI", "CS_1")
        print("change", cmd_sup.storage.current_object_is_new)
        print(cmd_sup.storage.current_object)

        cmd_sup.create_new_object("CoordinateSystemSOI")
        print("new", cmd_sup.storage.current_object_is_new)
        co = cmd_sup.storage.current_object
        print(co)
        print([getattr(co, attr_name) for attr_name in co.active_attrs])

        # cmd_sup.change_attribute_value("dependence", "dependent", -1)
        # print([getattr(co, attr_name) for attr_name in co.active_attrs])

        print("before apply", len(cmd_sup.storage.soi_objects["CoordinateSystemSOI"]))
        cmd_sup.apply_creation_new_object()
        print("after apply", len(cmd_sup.storage.soi_objects["CoordinateSystemSOI"]))

        print("before delete", [obj.name for obj in cmd_sup.storage.rectify_dg()])
        cmd_sup.delete_confirmed("CoordinateSystemSOI", "CS_2")
        print("after delete", [obj.name for obj in cmd_sup.storage.rectify_dg()])

        print("backward", cmd_sup.backward_args)

    test_20 = False
    if test_20:
        cmd_sup = CommandSupervisor()

        cmd_sup.read_station_config(STATION_IN_CONFIG_FOLDER)
        print([obj.name for obj in cmd_sup.storage.rectify_dg()])

        # print("before delete", [obj.name for obj in cmd_sup.storage.rectify_dg()])
        # cmd_sup.delete_confirmed("CoordinateSystemSOI", "CS_2")
        # print("after delete", [obj.name for obj in cmd_sup.storage.rectify_dg()])
        # cmd_sup.undo()
        # print("after undo", [obj.name for obj in cmd_sup.storage.rectify_dg()])

        cmd_sup.delete_request("CoordinateSystemSOI", "CS_2")

        # cmd_sup.change_current_object("CoordinateSystemSOI", "CS_1")
        # print("change", cmd_sup.storage.current_object_is_new)
        # print(cmd_sup.storage.current_object)

        # cmd_sup.change_current_object("CoordinateSystemSOI", "CS_2")
        # print("change", cmd_sup.storage.current_object_is_new)
        # print(cmd_sup.storage.current_object)
        #
        # cmd_sup.undo()
        # cmd_sup.undo()
        #
        # print("undo", cmd_sup.storage.current_object_is_new)
        # print(cmd_sup.storage.current_object)

        # cmd_sup.create_new_object("CoordinateSystemSOI")
        # print("new", cmd_sup.storage.current_object_is_new)
        # co = cmd_sup.storage.current_object
        # print(co)
        # print([getattr(co, attr_name) for attr_name in co.active_attrs])

        # cmd_sup.change_attribute_value("name", "Global_CS", -1)
        # print(co.name)
        # cmd_sup.change_attribute_value("name", "Global_CS1", -1)
        # print(co.name)
        # print([getattr(co, attr_name) for attr_name in co.active_attrs])

        # print("before apply", len(cmd_sup.storage.soi_objects["CoordinateSystemSOI"]))
        # cmd_sup.apply_creation_new_object()
        # print("after apply", len(cmd_sup.storage.soi_objects["CoordinateSystemSOI"]))
        #
        # cmd_sup.undo()
        # print("after undo", len(cmd_sup.storage.soi_objects["CoordinateSystemSOI"]))
        # cmd_sup.redo()
        # print("after redo", len(cmd_sup.storage.soi_objects["CoordinateSystemSOI"]))
        # print(co.name)
        # print([getattr(co, attr_name) for attr_name in co.active_attrs])

        # print("undo", cmd_sup.storage.current_object_is_new)
        # print(cmd_sup.storage.current_object)
