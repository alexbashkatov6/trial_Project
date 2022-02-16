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
    initialize = 0
    load_from_file = 1
    create_new_object = 2
    change_current_object = 3
    change_attrib_value = 4
    load_after_deletion = 5


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
    def __init__(self, start_command: Command):
        self.cmd_chain = [start_command]

    def append_command(self, command: Command):
        self.cmd_chain.append(command)

    def cut_slice(self, command: Command):
        """ command included in list"""
        self.cmd_chain = self.cmd_chain[:self.cmd_chain.index(command) + 1]

    def index_command_in_chain(self, command: Command) -> int:
        if command not in self.cmd_chain:
            return -1
        return self.cmd_chain.index(command)


class CommandSupervisor:
    def __init__(self):
        # commands state
        self.command_chains: list[CommandChain] = []
        self.command_pointer = None

        # functional classes
        self.storage = StorageDG()
        self.model = ModelBuilder()

        # current state variables
        self.apply_readiness = False
        self.new_stable_images = []
        self.deletion_names = []
        self.init_chains()

    def init_chains(self):
        cc = CommandChain(Command(CECommand(CECommand.initialize), []))
        self.command_chains.append(cc)
        self.command_pointer = cc.cmd_chain[-1]
        self.execute_commands()

    def reset_storages(self):
        self.storage.reset_storages()
        self.model.reset_storages()

    def model_building(self, images: list[StationObjectImage]):
        self.model.init_soi_list(images)
        self.model.build_skeleton()
        self.model.eval_link_length()
        self.model.build_lights()
        self.model.build_rail_points()
        self.model.build_borders()
        self.model.build_sections()

    def execute_command(self, command: Command) -> list[StationObjectImage]:
        new_images = self.soi_iast.copied_soi_objects

        if command.cmd_type == CECommand.initialize:
            pass

        if command.cmd_type == CECommand.load_from_file:
            dir_name = command.cmd_args[0]
            # new_images = [self.soi_iast.gcs]
            new_images.extend(read_station_config(dir_name))

        if command.cmd_type == CECommand.create_new_object:
            cls_name = command.cmd_args[0]
            self.soi_iast.create_new_object(cls_name)
            new_images.append(self.soi_iast.current_object)

        if command.cmd_type == CECommand.change_current_object:
            obj_name = command.cmd_args[0]
            self.soi_iast.set_current_object(obj_name)

        if command.cmd_type == CECommand.change_attrib_value:
            attr_name = command.cmd_args[0]
            new_attr_value = command.cmd_args[1]
            if self.soi_iast.curr_obj_is_new:
                setattr(self.soi_iast.current_object, attr_name, new_attr_value)
                new_images.append(self.soi_iast.current_object)
            else:
                current_obj = single_element(lambda x: x.name == self.soi_iast.current_object.name, new_images)
                if attr_name != "name":
                    setattr(current_obj, attr_name, new_attr_value)
                else:
                    new_images = self.model.rectifier.rename_object(current_obj.name, new_attr_value)

        if command.cmd_type == CECommand.load_after_deletion:
            new_images = command.cmd_args[0]

        return new_images

    def execute_commands(self):
        last_command = False
        if self.command_pointer:
            for chain in self.command_chains:
                if chain.index_command_in_chain(self.command_pointer) == -1:
                    continue
                for command in chain.cmd_chain:
                    old_images = self.soi_iast.copied_soi_objects
                    new_images = self.execute_command(command)
                    if command is self.command_pointer:
                        self.apply_readiness = False
                        if (command.cmd_type == CECommand.load_from_file) or \
                                (command.cmd_type == CECommand.load_after_deletion):
                            self.model.rectifier.batch_load_mode = True
                            try:
                                self.model_building(new_images)
                            except (DependenciesBuildError, AttributeEvaluateError) as e:
                                cls_name, obj_name, attr_name, comment = e.args
                                self.error_handler(cls_name, obj_name, attr_name, comment)
                                self.model_building(old_images)
                            except ModelBuildError as e:
                                cls_name, obj_name, comment = e.args
                                self.error_handler(cls_name, obj_name, "", comment)
                                self.model_building(old_images)
                            else:
                                self.new_stable_images = new_images
                                self.apply_readiness = True
                                self.apply_changes()
                                self.soi_iast.reset_current_object()
                            finally:
                                self.model.rectifier.batch_load_mode = False
                        else:
                            try:
                                self.model_building(new_images)
                            except (DependenciesBuildError, AttributeEvaluateError) as e:
                                cls_name, obj_name, attr_name, comment = e.args
                                self.error_handler(cls_name, obj_name, attr_name, comment)
                            except ModelBuildError as e:
                                cls_name, obj_name, comment = e.args
                                self.error_handler(cls_name, obj_name, "", comment)
                            else:
                                self.new_stable_images = new_images
                                self.apply_readiness = True
                            finally:
                                self.model_building(old_images)
                        last_command = True
                        break
                if last_command:
                    break

    def error_handler(self, cls_name: str, obj_name: str, attr_name: str, message: str):
        if cls_name.endswith("SOI"):
            cls_name = cls_name.replace("SOI", "")
        print("Attribute error! \ncls_name: {} \nobj_name: {} \nattr_name: {}\n message: {}"
              .format(cls_name, obj_name, attr_name, message))

    def cut_slice(self, chain: CommandChain):
        self.command_chains = self.command_chains[:self.command_chains.index(chain)+1]

    def continue_commands(self, new_command: Command):
        chain_with_pointer = None
        if self.command_pointer:
            for chain in self.command_chains:
                if chain.index_command_in_chain(self.command_pointer) != -1:
                    chain_with_pointer = chain
                    chain.cut_slice(self.command_pointer)
                    chain.append_command(new_command)
                    self.command_pointer = new_command
                    break
            assert chain_with_pointer, "chain not found"
            self.cut_slice(chain_with_pointer)
            self.execute_commands()

    def undo(self):
        """ not most effective realisation """
        self.reset_storages()
        pointer_found = False
        if self.command_pointer:

            for chain in reversed(self.command_chains):
                if pointer_found:
                    self.command_pointer = chain.cmd_chain[-1]
                    self.execute_commands()
                    return
                if chain.index_command_in_chain(self.command_pointer) != -1:
                    index = chain.cmd_chain.index(self.command_pointer)
                    if index != 0:
                        self.command_pointer = chain.cmd_chain[index - 1]
                        self.execute_commands()
                        return
                    else:
                        pointer_found = True
                        continue
            assert pointer_found, "command_pointer not found in chains"
            print("CANNOT UNDO")

    def redo(self):
        self.reset_storages()
        pointer_found = False
        if self.command_pointer:
            for chain in self.command_chains:
                if pointer_found:
                    self.command_pointer = chain.cmd_chain[0]
                    self.execute_commands()
                    return
                if chain.index_command_in_chain(self.command_pointer) != -1:
                    index = chain.cmd_chain.index(self.command_pointer)
                    if index != len(chain.cmd_chain)-1:
                        self.command_pointer = chain.cmd_chain[index + 1]
                        self.execute_commands()
                        return
                    else:
                        pointer_found = True
                        continue
            assert pointer_found, "command_pointer not found in chains"
            print("CANNOT REDO")

    """ High-level interface operations - by 'buttons' """

    def read_station_config(self, dir_name: str):
        cc = CommandChain(Command(CECommand(CECommand.load_from_file),
                                  [dir_name]))
        self.command_chains.append(cc)
        self.command_pointer = cc.cmd_chain[-1]
        self.execute_commands()

    def eval_routes(self, train_xml: str, shunt_xml: str):
        self.model.eval_routes(train_xml, shunt_xml)

    def create_new_object(self, cls_name: str):
        self.continue_commands(Command(CECommand(CECommand.create_new_object), [cls_name]))

    def change_current_object(self, name: str):
        self.continue_commands(Command(CECommand(CECommand.change_current_object), [name]))

    def change_attribute_value(self, attr_name: str, new_value: str):
        self.continue_commands(Command(CECommand(CECommand.change_attrib_value), [attr_name, new_value]))

    def apply_changes(self):
        assert self.apply_readiness, "No readiness for apply"
        self.soi_iast.soi_objects = self.new_stable_images
        self.model_building(self.new_stable_images)

    def delete_obj(self, obj_name: str):
        assert obj_name != GLOBAL_CS_NAME, "Cannot delete GCS"
        self.deletion_names = self.model.rectifier.dependent_objects_names(obj_name)
        self.deletion_warning()

    def deletion_warning(self):
        print("Will be deleted: ", self.deletion_names)

    def deletion_approved(self):
        images_after_deletion = [obj for obj in self.soi_iast.copied_soi_objects if obj.name not in self.deletion_names]
        cc = CommandChain(Command(CECommand(CECommand.load_after_deletion),
                                  [images_after_deletion]))
        self.command_chains.append(cc)
        self.command_pointer = cc.cmd_chain[-1]
        self.execute_commands()
        self.deletion_names = []

    def deletion_rejected(self):
        self.deletion_names = []


if __name__ == "__main__":

    test_14 = False
    if test_14:
        cmd_sup = CommandSupervisor()
        cmd_sup.read_station_config(STATION_IN_CONFIG_FOLDER)
        cmd_sup.read_station_config(STATION_IN_CONFIG_FOLDER)
        cmd_sup.undo()
        # cmd_sup.undo()
        print("command_pointer", cmd_sup.command_pointer)
        print([command_chain.cmd_chain for command_chain in cmd_sup.command_chains])
        cmd_sup.eval_routes("TrainRoute.xml", "ShuntingRoute.xml")

    test_15 = False
    if test_15:
        cmd_sup = CommandSupervisor()
        cmd_sup.create_new_object("CoordinateSystemSOI")
        # cmd_sup.create_new_object("AxisSOI")
        # cmd_sup.create_new_object("LineSOI")
        curr_obj = cmd_sup.soi_iast.current_object
        curr_obj.x = "5"
        print(curr_obj)
        print(curr_obj._str_x)
        cmd_sup.undo()
        curr_obj_after_undo = cmd_sup.soi_iast.current_object
        print()
        print(curr_obj_after_undo)

    test_16 = False
    if test_16:
        cmd_sup = CommandSupervisor()
        cmd_sup.create_new_object("CoordinateSystemSOI")
        cmd_sup.change_attribute_value("x", "5")
        curr_obj = cmd_sup.soi_iast.current_object
        print(curr_obj)
        print(curr_obj._str_x)

    test_17 = False
    if test_17:
        # print(cmd_sup.soi_iast.current_object.__dict__)
        cmd_sup = CommandSupervisor()
        print("create_new")
        cmd_sup.create_new_object("CoordinateSystemSOI")
        print("name")
        cmd_sup.change_attribute_value("name", "MyCS_1")
        print("cs_relative_to")
        cmd_sup.change_attribute_value("cs_relative_to", "GlobalCS")
        print("x")
        cmd_sup.change_attribute_value("x", "0")
        cmd_sup.apply_changes()

        print("create_new")
        cmd_sup.create_new_object("CoordinateSystemSOI")
        print("name")
        cmd_sup.change_attribute_value("name", "MyCS_2")
        print("cs_relative_to")
        cmd_sup.change_attribute_value("cs_relative_to", "MyCS_1")
        print("x")
        cmd_sup.change_attribute_value("x", "0")
        cmd_sup.apply_changes()

        # print("dependent", cmd_sup.model.rectifier.dependent_objects_names("MyCS_2"))
        # print("change_current_object")
        # cmd_sup.change_current_object("MyCS_1")
        # print("cs_relative_to")
        # cmd_sup.change_attribute_value("cs_relative_to", "MyCS_2")
        # cmd_sup.apply_changes()

        # cmd_sup.delete_obj("MyCS_2")
        # cmd_sup.deletion_approved()

        print("change_current_object")
        cmd_sup.change_current_object("MyCS_1")
        print("name")
        cmd_sup.change_attribute_value("name", "MyCS_0")
        cmd_sup.apply_changes()

        print("names", [obj.name for obj in cmd_sup.soi_iast.soi_objects])
        MyCS_2 = cmd_sup.soi_iast.get_obj_by_name("MyCS_2")
        print("MyCS_2 cs = ", MyCS_2.cs_relative_to.name)

        dg = cmd_sup.model.rectifier.dg
        print(len(dg.nodes))
        print(len(dg.links))
        print(dg.links)

    test_18 = True
    if test_18:
        pass