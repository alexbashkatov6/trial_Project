from __future__ import annotations
from collections import OrderedDict
import os
import pandas as pd

from custom_enum import CustomEnum
from soi_interactive_storage import SOIInteractiveStorage
from soi_rectifier import DependenciesBuildError
from soi_attributes_evaluations import AttributeEvaluateError
from mo_model_builder import ModelBuilder, ModelBuildError
from soi_objects import StationObjectImage
from extended_itertools import single_element

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


def read_station_config(dir_name: str) -> list[StationObjectImage]:
    result = []
    folder = os.path.join(os.getcwd(), dir_name)
    for cls in StationObjectImage.__subclasses__():
        name_soi = cls.__name__
        name_del_soi = name_soi.replace("SOI", "")
        file = os.path.join(folder, "{}.xlsx".format(name_del_soi))
        df: pd.DataFrame = pd.read_excel(file, dtype=str, keep_default_na=False)
        obj_dict_list: list[OrderedDict] = df.to_dict('records', OrderedDict)
        for obj_dict in obj_dict_list:
            new_obj = cls()
            for attr_name, attr_val in obj_dict.items():
                attr_name: str
                attr_val: str
                attr_name = attr_name.strip()
                attr_val = attr_val.strip()
                setattr(new_obj, attr_name, attr_val)
            result.append(new_obj)
    return result


class CommandSupervisor:
    def __init__(self):
        self.command_chains: list[CommandChain] = []
        self.command_pointer = None
        self.soi_iast = SOIInteractiveStorage()
        self.model = ModelBuilder()
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
        self.soi_iast.reset_storages()
        self.model.reset_storages()

    def model_building(self, images: list[StationObjectImage]):
        self.model.build_dg(images)
        self.model.evaluate_attributes()
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
            new_images = [self.soi_iast.gcs]
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

# def execute_commands(commands: list[Command]):
#     for command in commands:
#         if command.cmd_type == CECommand.load_from_file:
#             dir_name = command.cmd_args[0]
#             SOI_IS.read_station_config(dir_name)
#             images = SOI_IS.soi_objects
#             MODEL.build_dg(images)
#             MODEL.evaluate_attributes()
#             MODEL.build_skeleton()
#             MODEL.eval_link_length()
#             MODEL.build_lights()
#             MODEL.build_rail_points()
#             MODEL.build_borders()
#             MODEL.build_sections()


if __name__ == "__main__":

    # test_3 = False
    # if test_3:
    #     pnt = PointSOI()
    #     pnt.x = "PK_12+34"
    #     print(type(pnt.x))
    #     print(pnt.x)
    #     print(PointSOI.attr_sequence_template)
    #
    # test_4 = False
    # if test_4:
    #     cs = CoordinateSystemSOI()
    #     print(CoordinateSystemSOI.dict_possible_values)
    #     print(cs.dict_possible_values)
    #
    # test_5 = False
    # if test_5:
    #     make_xlsx_templates(STATION_OUT_CONFIG_FOLDER)
    #
    # test_6 = False
    # if test_6:
    #     objs = read_station_config(STATION_IN_CONFIG_FOLDER)
    #     # pnt = get_object_by_name("Point_15", objs)
    #     print(pnt.dict_possible_values)
    #     print(pnt.__class__.dict_possible_values)
    #     # for attr_ in pnt.active_attrs:
    #     #     print(getattr(pnt, attr_))
    #
    # test_7 = False
    # if test_7:
    #     pnt = PointSOI()
    #     pnt.x = "PK_12+34"
    #     print(pnt.x)
    #
    # test_8 = False
    # if test_8:
    #     objs = read_station_config(STATION_IN_CONFIG_FOLDER)
    #     # SOIR.build_dg(objs)
    #     # SOIR.check_cycle()
    #     # print([obj.name for obj in SOIR.rectified_object_list()])
    #     # build_model(SOIR.rectified_object_list())
    #
    # test_9 = False
    # if test_9:
    #     execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
    #     print(MODEL.names_soi)
    #     print(MODEL.names_mo)
    #
    #     # cs_1: CoordinateSystemMO = MODEL.names_mo['CS_1']
    #     # print(cs_1.absolute_x)
    #     # print(cs_1.absolute_y)
    #     # print(cs_1.absolute_co_x)
    #     # print(cs_1.absolute_co_y)
    #     # if 'CS_2' in MODEL.names_mo:
    #     #     cs_2 = MODEL.names_mo['CS_2']
    #     #     print(cs_2.absolute_x)
    #     #     print(cs_2.absolute_y)
    #     #     print(cs_2.absolute_co_x)
    #     #     print(cs_2.absolute_co_y)
    #     # if 'CS_3' in MODEL.names_mo:
    #     #     cs_3 = MODEL.names_mo['CS_3']
    #     #     print(cs_3.absolute_x)
    #     #     print(cs_3.absolute_y)
    #     #     print(cs_3.absolute_co_x)
    #     #     print(cs_3.absolute_co_y)
    #
    #     ax_1: AxisMO = MODEL.names_mo['Axis_1']
    #     print(ax_1.line2D)
    #
    #     line_2: LineMO = MODEL.names_mo['Line_7']
    #     print(line_2.boundedCurves)
    #
    #     # pnt_15: PointMO = MODEL.names_mo['Axis_1']
    #     # print(ax_1.line2D)
    #
    # test_10 = False
    # if test_10:
    #
    #     execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
    #     print(MODEL.names_soi)
    #     # print(MODEL.names_soi.keys())  # .rect_so
    #     print(MODEL.rect_so)
    #     print(MODEL.names_mo)
    #
    #     # line_1_node = get_point_node_DG("Line_1")
    #     # line_6_node = get_point_node_DG("Line_6")
    #     # point_16_node = get_point_node_DG("Point_16")
    #     # print("line_1_node", line_1_node)
    #     # print("line_6_node", line_6_node)
    #     # print("line_6 up connections", [link.opposite_ni(line_6_node.ni_pu).pn for link in line_6_node.ni_pu.links])
    #     # print("point_16_node", point_16_node)
    #     # print("point_16 up connections", [link.opposite_ni(point_16_node.ni_pu).pn
    #     for link in point_16_node.ni_pu.links])
    #     #
    #     # print(MODEL.dg.longest_coverage())
    #     # print("len routes", len(MODEL.dg.walk(MODEL.dg.inf_pu.ni_nd)))
    #     # i=0
    #     # for route in MODEL.dg.walk(MODEL.dg.inf_pu.ni_nd):
    #     #     if (line_6_node in route.nodes) or (line_6_node in route.nodes):
    #     #         i+=1
    #     #         print("i=", i)
    #     #         print("nodes", route.nodes)
    #
    #     # ax_1: AxisMO = MODEL.names_mo['Axis_2']
    #     # print([pnt.x for pnt in ax_1.points])
    #     print(len(MODEL.smg.not_inf_nodes))
    #
    #     print("minus inf", MODEL.smg.inf_nd)
    #     print("plus inf", MODEL.smg.inf_pu)
    #     for i in range(20):
    #         try:
    #             pnt_name = "Point_{}".format(str(i+1))
    #             pnt_node: PolarNode = find_cell_name(MODEL.smg.not_inf_nodes, PointCell, pnt_name)[1]
    #             print(pnt_name+" =>", pnt_node)
    #             print("nd-connections", [link.opposite_ni(pnt_node.ni_nd).pn for link in pnt_node.ni_nd.links])
    #             print("pu-connections", [link.opposite_ni(pnt_node.ni_pu).pn for link in pnt_node.ni_pu.links])
    #         except NotFoundCellError:
    #             continue
    #     print("len of links", len(MODEL.smg.links))
    #     for link in MODEL.smg.not_inf_links:
    #         print()
    #         ni_s = link.ni_s
    #         pn_s = [ni.pn for ni in link.ni_s]
    #         pnt_cells: list[PointCell] = [element_cell_by_type(pn, PointCell) for pn in pn_s]
    #         print("link between {}, {}".format(pnt_cells[0].name, pnt_cells[1].name))
    #         print("length {}".format(element_cell_by_type(link, LengthCell).length))
    #         for ni in ni_s:
    #             move = ni.get_move_by_link(link)
    #             if move.cell_objs:
    #                 rpdc = element_cell_by_type(move, RailPointDirectionCell)
    #                 print("Rail point direction = ", rpdc.direction)
    #         print("section {}".format(element_cell_by_type(link, IsolatedSectionCell).name))
    #
    # test_11 = False
    # if test_11:
    #     execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
    #     light_cells = all_cells_of_type(MODEL.smg.not_inf_nodes, LightCell)
    #     print(len(light_cells))

    test_12 = False
    if test_12:
        pass
        # execute_commands([Command(CECompositeCommand(CECompositeCommand.load_from_file), [STATION_IN_CONFIG_FOLDER])])
        # MODEL.eval_routes("TrainRoute.xml", "ShuntingRoute.xml")

    test_13 = False
    if test_13:
        pass
        # class Command:
        #     def __init__(self, name: str):
        #         self.name = name
        #
        #     def __repr__(self):
        #         return "{}('{}')".format(self.__class__.__name__, self.name)
        #
        #     __str__ = __repr__

        # cmd_sup = CommandSupervisor()
        # cmd_sup.save_state(SOI_IS)
        # print("pointer = ", cmd_sup.command_pointer)
        # cmd_sup.continue_commands(Command("1"))
        # print("pointer = ", cmd_sup.command_pointer)
        # cmd_sup.continue_commands(Command("2"))
        # print("pointer = ", cmd_sup.command_pointer)
        # cmd_sup.save_state(SOI_IS)
        # print("pointer = ", cmd_sup.command_pointer)
        # cmd_sup.continue_commands(Command("3"))
        # print("pointer = ", cmd_sup.command_pointer)
        # cmd_sup.continue_commands(Command("4"))
        # print("pointer = ", cmd_sup.command_pointer)
        # print([command_chain.cmd_chain for command_chain in cmd_sup.command_chains])
        # cmd_sup.undo()
        # print()
        # cmd_sup.undo()
        # print()
        # cmd_sup.undo()
        # print()
        # cmd_sup.undo()
        # print()
        # cmd_sup.undo()
        # print()
        # cmd_sup.undo()
        # print()
        # cmd_sup.continue_commands(Command("5"))
        # print("pointer = ", cmd_sup.command_pointer)
        # print([command_chain.cmd_chain for command_chain in cmd_sup.command_chains])

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

    test_17 = True
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