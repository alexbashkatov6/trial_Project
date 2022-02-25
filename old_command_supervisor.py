from __future__ import annotations
from collections import OrderedDict
import os
import pandas as pd
from typing import Optional, Any, Union

from custom_enum import CustomEnum
from old_soi_rectifier import StorageDG, DependenciesBuildError
from old_model_builder import ModelBuilder, ModelBuildError
from soi_objects import StationObjectImage, AttributeEvaluateError, AttribValues
from extended_itertools import single_element
from soi_files_handler import read_station_config, ReadFileNameError
from form_exception_message import form_message_from_error
from default_ordered_dict import DefaultOrderedDict
from attribute_data import AttributeErrorData
from soi_metadata import ObjectProperties, ComplexAttribProperties, SingleAttribProperties

from config_names import STATION_IN_CONFIG_FOLDER, GLOBAL_CS_NAME


# class AttributeSoiError(Exception):
#     pass
#
#
# class ObjectSoiError(Exception):
#     pass


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
        self.executed = False


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
        self.apply_readiness = False

        # objs dict
        self.objs_dict_changed = False
        self.objs_dict: DefaultOrderedDict[str, OrderedDict[str, dict[str, Any]]] = \
            DefaultOrderedDict(OrderedDict)

        # check statuses
        self.object_check: str = ""
        self.common_status: str = ""
        self.error_message: str = ""

        # delete state variables
        self.deletion_names = []
        self.delete_request_name: Optional[tuple[str, str]] = None

        self.model_building(self.storage.rectify_dg())

    def form_cls_obj_dict(self):
        self.objs_dict_changed = True
        self.objs_dict = DefaultOrderedDict(OrderedDict)
        soi = self.storage.soi_objects
        for cls_name in soi:
            cls_name_str = cls_name.replace("SOI", "")
            self.objs_dict[cls_name_str] = OrderedDict()
            for obj_name in soi[cls_name]:
                obj: StationObjectImage = soi[cls_name][obj_name]
                od_struct = {"attributes": OrderedDict(), "error_status": ""}
                for attr_name in obj.active_attrs:
                    attr_value: Union[AttribValues, list[AttribValues]] = getattr(obj, attr_name)
                    if isinstance(attr_value, list):
                        for i, attr_val in enumerate(attr_value):
                            od_struct["attributes"]["{}_{}".format(attr_name, i + 1)] = self.str_values_logic(attr_val)
                    else:
                        od_struct["attributes"][attr_name] = self.str_values_logic(attr_value)
                self.objs_dict[cls_name_str][obj_name] = od_struct

    def str_values_logic(self, attr_value: Union[AttribValues, list[AttribValues]]) -> str:
        last_imp_val = attr_value.last_input_value
        conf_val = attr_value.str_confirmed_value
        # sugg_val = attr_value.suggested_value
        if conf_val:
            return conf_val
        # elif sugg_val:
        #     return sugg_val
        else:
            return last_imp_val

    def model_building(self, images: list[StationObjectImage]):
        print("model_building")
        self.model.init_soi_list(images)
        self.model.build_skeleton()
        self.model.eval_link_length()
        self.model.build_lights()
        self.model.build_rail_points()
        self.model.build_borders()
        self.model.build_sections()

    def execute_command_at_pointer(self):
        self.execute_command(self.commands[self.command_index])

    def execute_command(self, command) -> Optional[list[Any]]:

        if command.cmd_type == CECommand.create_new_object:
            cls_name = command.cmd_args[0]
            old_obj_params = self.storage.create_empty_new_object(cls_name)
            old_cls_name, old_obj_name = old_obj_params
            backward_arg = [old_cls_name, old_obj_name]
            return backward_arg

        if command.cmd_type == CECommand.change_current_object:
            cls_name = command.cmd_args[0]
            obj_name = command.cmd_args[1]
            old_obj_params = self.storage.select_current_object(cls_name, obj_name)
            old_cls_name, old_obj_name = old_obj_params
            backward_arg = [old_cls_name, old_obj_name]
            return backward_arg

        if command.cmd_type == CECommand.delete_obj:
            cls_name = command.cmd_args[0]
            obj_name = command.cmd_args[1]
            recover_obj_dict = self.storage.delete_object(cls_name, obj_name)
            self.form_cls_obj_dict()
            backward_arg = [recover_obj_dict]
            return backward_arg

        if command.cmd_type == CECommand.load_from_file:
            dir_name = command.cmd_args[0]

            try:
                new_objects = read_station_config(dir_name)
            except ReadFileNameError as e:
                self.common_status = form_message_from_error(e)
                self.error_message = form_message_from_error(e)
                return

            self.storage.save_state()
            self.form_cls_obj_dict()
            backward_arg = [self.storage.backup_soi]

            try:
                self.storage.reload_from_dict(new_objects)
            except DependenciesBuildError as e:
                self.form_error_objects(e)
                self.common_status = form_message_from_error(e)
                self.error_message = form_message_from_error(e)
                return backward_arg

            try:
                self.model_building(self.storage.rectify_dg())
            except ModelBuildError as e:
                self.form_error_objects(e)
                self.common_status = form_message_from_error(e)
                self.error_message = form_message_from_error(e)
                return backward_arg

            self.form_cls_obj_dict()
            self.common_status = "Objects successfully loaded from file"
            return backward_arg

        if command.cmd_type == CECommand.apply_creation_new_object:
            cls_name, obj_name = self.storage.apply_creation_current_object()
            backward_arg = [cls_name, obj_name]
            return backward_arg

        if command.cmd_type == CECommand.change_attrib_value:
            attr_name = command.cmd_args[0]
            new_value = command.cmd_args[1]
            index = command.cmd_args[2]
            old_value = self.storage.change_attrib_value_main(attr_name, new_value, index)
            backward_arg = [attr_name, old_value, index]
            return backward_arg

    def form_error_objects(self, e: Exception):
        self.form_cls_obj_dict()
        ad_list = e.args[1]
        if not isinstance(ad_list, list):
            ad_list = [ad_list]
        for ad in ad_list:
            ad: AttributeErrorData
            self.objs_dict[ad.cls_name.replace("SOI", "")][ad.obj_name]["error_status"] = e.args[0]

    def try_execute_command(self, command):
        backward_arg = self.execute_command(command)
        if backward_arg:

            """ continue list of commands """
            cur_len = len(self.commands)
            for i in reversed(range(self.command_index+1, cur_len)):
                self.commands.pop(i)
            self.commands.append(command)
            self.command_index = len(self.commands)-1

            """ continue list of backward args """
            assert len(self.backward_args) >= self.command_index
            if len(self.backward_args) == self.command_index:
                self.backward_args.append(backward_arg)
            else:
                self.backward_args[self.command_index] = backward_arg

    def undo(self):
        if self.command_index == -1:
            self.common_status = "CANNOT UNDO"
            return
        command = self.commands[self.command_index]
        back_args = self.backward_args[self.command_index]
        if command.cmd_type == CECommand.load_from_file:
            self.storage.reload_from_dict(*back_args)
            self.form_cls_obj_dict()
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
            self.common_status = "CANNOT REDO"
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
        c = Command(CECommand(CECommand.load_from_file), [dir_name])
        self.try_execute_command(c)

    def create_new_object(self, cls_name: str):
        c = Command(CECommand(CECommand.create_new_object), [cls_name])
        self.try_execute_command(c)

    def change_current_object(self, cls_name: str, obj_name: str):
        c = Command(CECommand(CECommand.change_current_object), [cls_name, obj_name])
        self.try_execute_command(c)

    def change_attribute_value(self, attr_name: str, new_value: str, index: int):
        c = Command(CECommand(CECommand.change_attrib_value), [attr_name, new_value, index])
        self.try_execute_command(c)

    def apply_creation_new_object(self):
        c = Command(CECommand(CECommand.apply_creation_new_object), [])
        self.try_execute_command(c)

    def delete_request(self, cls_name: str, obj_name: str):
        self.delete_request_name = (cls_name, obj_name)
        self.deletion_names = self.storage.dependent_objects_names(cls_name, obj_name)

    def delete_confirmed(self):
        cls_name, obj_name = self.delete_request_name
        print("deleted:", self.deletion_names)
        self.delete_request_name = None
        self.deletion_names = []
        c = Command(CECommand(CECommand.delete_obj), [cls_name, obj_name])
        self.try_execute_command(c)

    def form_attributes(self):
        pass

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
