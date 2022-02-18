from __future__ import annotations
from collections import OrderedDict
import os
import pandas as pd

from custom_enum import CustomEnum
# from soi_interactive_storage import SOIInteractiveStorage
from new_soi_rectifier import StorageDG, DependenciesBuildError
from soi_attributes_evaluations import AttributeEvaluateError
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
        """ Commands have next formats:
        load_from_file(objects)  # Command(CECommand(CECommand.load_from_file), [])
        create_object(cls_name)  # Command(CECommand(CECommand.create_object), [cls_name])
        rename_object(old_name, new_name)
        change_attrib_value(obj_name, attr_name, new_value)
        delete_object(obj_name)
        """
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


"""
Command(CECommand(CECommand.load_from_file), [dir_name]) => 
new_objs = read_station_config(dir_name)
redo : reset_objs = reload_from_dict(new_objs)
undo : reload_from_dict(reset_objs)

Command(CECommand(CECommand.create_new_object), [cls_name]) => 
redo : old_cls_name, old_obj_name = create_empty_new_object(cls_name)
undo : select_current_object(old_cls_name, old_obj_name)

Command(CECommand(CECommand.change_current_object), [cls_name, obj_name]) => 
redo : old_cls_name, old_obj_name = select_current_object(cls_name, obj_name)
undo : select_current_object(old_cls_name, old_obj_name)

Command(CECommand(CECommand.apply_creation_new_object), []) => 
redo : cls_name, obj_name = apply_creation_current_object()
undo : delete_object(cls_name, obj_name)

Command(CECommand(CECommand.delete_obj), [cls_name, obj_name]) => 
redo : del_obj_dict = delete_object(cls_name, obj_name)
undo : recover_objects(del_obj_dict)

Command(CECommand(CECommand.change_attrib_value), [attr_name, new_value, index]) => 
redo : old_value = change_attrib_value_main(attr_name, new_value, index)
undo : change_attrib_value_main(attr_name, old_value, index)
"""


class CommandSupervisor:
    def __init__(self):
        # commands state
        self.commands = []  # CommandChain()
        self.backward_args = []
        self.command_pointer = None

        # functional classes
        self.storage = StorageDG()
        self.model = ModelBuilder()

        # current state variables
        self.apply_readiness = False
        self.new_stable_images = []
        self.deletion_names = []

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

    def execute_last_command(self):
        command = self.commands[-1]
        if command.cmd_type == CECommand.load_from_file:
            dir_name = command.cmd_args[0]
            new_objects = read_station_config(dir_name)
            reset_objects = self.storage.reload_from_dict(new_objects)
            self.backward_args.append([reset_objects])
        if command.cmd_type == CECommand.create_new_object:
            cls_name = command.cmd_args[0]
            old_cls_name, old_obj_name = self.storage.create_empty_new_object(cls_name)
            self.backward_args.append([old_cls_name, old_obj_name])
        if command.cmd_type == CECommand.change_current_object:
            cls_name = command.cmd_args[0]
            obj_name = command.cmd_args[1]
            old_cls_name, old_obj_name = self.storage.select_current_object(cls_name, obj_name)
            self.backward_args.append([old_cls_name, old_obj_name])
        if command.cmd_type == CECommand.apply_creation_new_object:
            cls_name, obj_name = self.storage.apply_creation_current_object()
            self.backward_args.append([cls_name, obj_name])
        if command.cmd_type == CECommand.delete_obj:
            cls_name = command.cmd_args[0]
            obj_name = command.cmd_args[1]
            recover_obj_dict = self.storage.delete_object(cls_name, obj_name)
            self.backward_args.append([recover_obj_dict])
        if command.cmd_type == CECommand.change_attrib_value:
            attr_name = command.cmd_args[0]
            new_value = command.cmd_args[1]
            index = command.cmd_args[2]
            old_value = self.storage.change_attrib_value_main(attr_name, new_value, index)
            self.backward_args.append([attr_name, old_value, index])

    # def error_handler(self, cls_name: str, obj_name: str, attr_name: str, message: str):
    #     if cls_name.endswith("SOI"):
    #         cls_name = cls_name.replace("SOI", "")
    #     print("Attribute error! \ncls_name: {} \nobj_name: {} \nattr_name: {}\n message: {}"
    #           .format(cls_name, obj_name, attr_name, message))
    #
    # def cut_slice(self, chain: CommandChain):
    #     self.command_chains = self.command_chains[:self.command_chains.index(chain)+1]
    #
    # def continue_commands(self, new_command: Command):
    #     chain_with_pointer = None
    #     if self.command_pointer:
    #         for chain in self.command_chains:
    #             if chain.index_command_in_chain(self.command_pointer) != -1:
    #                 chain_with_pointer = chain
    #                 chain.cut_slice(self.command_pointer)
    #                 chain.append_command(new_command)
    #                 self.command_pointer = new_command
    #                 break
    #         assert chain_with_pointer, "chain not found"
    #         self.cut_slice(chain_with_pointer)
    #         self.execute_commands()
    #
    # def undo(self):
    #     """ not most effective realisation """
    #     self.reset_storages()
    #     pointer_found = False
    #     if self.command_pointer:
    #
    #         for chain in reversed(self.command_chains):
    #             if pointer_found:
    #                 self.command_pointer = chain.commands[-1]
    #                 self.execute_commands()
    #                 return
    #             if chain.index_command_in_chain(self.command_pointer) != -1:
    #                 index = chain.commands.index(self.command_pointer)
    #                 if index != 0:
    #                     self.command_pointer = chain.commands[index - 1]
    #                     self.execute_commands()
    #                     return
    #                 else:
    #                     pointer_found = True
    #                     continue
    #         assert pointer_found, "command_pointer not found in chains"
    #         print("CANNOT UNDO")
    #
    # def redo(self):
    #     self.reset_storages()
    #     pointer_found = False
    #     if self.command_pointer:
    #         for chain in self.command_chains:
    #             if pointer_found:
    #                 self.command_pointer = chain.commands[0]
    #                 self.execute_commands()
    #                 return
    #             if chain.index_command_in_chain(self.command_pointer) != -1:
    #                 index = chain.commands.index(self.command_pointer)
    #                 if index != len(chain.commands)-1:
    #                     self.command_pointer = chain.commands[index + 1]
    #                     self.execute_commands()
    #                     return
    #                 else:
    #                     pointer_found = True
    #                     continue
    #         assert pointer_found, "command_pointer not found in chains"
    #         print("CANNOT REDO")

    """ High-level interface operations - by 'buttons' """

    def read_station_config(self, dir_name: str):
        self.commands.append(Command(CECommand(CECommand.load_from_file), [dir_name]))
        self.command_pointer = self.commands[-1]
        self.execute_last_command()

    def eval_routes(self, train_xml: str, shunt_xml: str):
        self.model.eval_routes(train_xml, shunt_xml)
    #
    # def create_new_object(self, cls_name: str):
    #     self.continue_commands(Command(CECommand(CECommand.create_new_object), [cls_name]))
    #
    # def change_current_object(self, name: str):
    #     self.continue_commands(Command(CECommand(CECommand.change_current_object), [name]))
    #
    # def change_attribute_value(self, attr_name: str, new_value: str):
    #     self.continue_commands(Command(CECommand(CECommand.change_attrib_value), [attr_name, new_value]))
    #
    # def apply_changes(self):
    #     assert self.apply_readiness, "No readiness for apply"
    #     self.soi_iast.soi_objects = self.new_stable_images
    #     self.model_building(self.new_stable_images)
    #
    # def delete_obj(self, obj_name: str):
    #     assert obj_name != GLOBAL_CS_NAME, "Cannot delete GCS"
    #     self.deletion_names = self.model.rectifier.dependent_objects_names(obj_name)
    #     self.deletion_warning()
    #
    # def deletion_warning(self):
    #     print("Will be deleted: ", self.deletion_names)
    #
    # def deletion_approved(self):
    #     images_after_deletion = [obj for obj in self.soi_iast.copied_soi_objects if obj.name not in self.deletion_names]
    #     cc = CommandChain(Command(CECommand(CECommand.load_after_deletion),
    #                               [images_after_deletion]))
    #     self.command_chains.append(cc)
    #     self.command_pointer = cc.commands[-1]
    #     self.execute_commands()
    #     self.deletion_names = []
    #
    # def deletion_rejected(self):
    #     self.deletion_names = []


if __name__ == "__main__":

    test_18 = True
    if test_18:
        cmd_sup = CommandSupervisor()
        cmd_sup.read_station_config(STATION_IN_CONFIG_FOLDER)
        obj_list = cmd_sup.storage.rectify_dg()
        # print([obj.name for obj in obj_list])
        cmd_sup.model_building(obj_list)
        # print(cmd_sup.model.images)
        # print(len(cmd_sup.model.smg.not_inf_nodes))
        cmd_sup.eval_routes("TrainRoute.xml", "ShuntingRoute.xml")

