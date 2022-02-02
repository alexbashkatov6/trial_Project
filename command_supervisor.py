from __future__ import annotations
from copy import copy

from custom_enum import CustomEnum
from soi_interactive_storage import SOIInteractiveStorage
from soi_rectifier import DependenciesBuildError
from soi_attributes_evaluator import AttributeEvaluateError
from mo_model_builder import ModelBuilder
from soi_objects import StationObjectImage

from config_names import STATION_IN_CONFIG_FOLDER


class AttributeSoiError(Exception):
    pass


class ObjectSoiError(Exception):
    pass


# class CEElementaryCommand(CustomEnum):
#     create_object = 0
#     change_attrib_value = 1
#     elementary_delete_object = 2


class CECommand(CustomEnum):
    load_objects = 0
    create_new_object = 1
    change_current_object = 2
    rename_object = 3
    change_attrib_value = 4
    delete_object = 5


class Command:
    def __init__(self, cmd_type: CECommand, cmd_args: list):
        """ Commands have next formats:
        load_objects(objects)  # Command(CECommand(CECommand.load_objects), [])
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
        self.command_chains: list[CommandChain] = []
        self.command_pointer = None
        self.soi_is = SOIInteractiveStorage()
        self.model = ModelBuilder()
        self.save_state()

    def reset_storages(self):
        self.soi_is.reset_storages()
        self.model.reset_storages()

    def execute_commands(self):
        last_command = False
        if self.command_pointer:
            for chain in self.command_chains:
                if chain.index_command_in_chain(self.command_pointer) == -1:
                    continue
                for command in chain.cmd_chain:
                    self.execute_command(command)
                    if command is self.command_pointer:
                        last_command = True
                        break
                if last_command:
                    break

    def model_building(self, images: list[StationObjectImage]):
        self.model.build_dg(images)
        self.model.evaluate_attributes()
        self.model.build_skeleton()
        self.model.eval_link_length()
        self.model.build_lights()
        self.model.build_rail_points()
        self.model.build_borders()
        self.model.build_sections()

    def execute_command(self, command: Command):
        old_images = self.soi_is.copied_soi_objects
        new_images: list[StationObjectImage] = []
        attr_name = "name"

        if command.cmd_type == CECommand.load_objects:
            new_images = command.cmd_args[0]

        if command.cmd_type == CECommand.create_new_object:
            cls_name = command.cmd_args[0]
            self.soi_is.create_new_object(cls_name)
            new_images = copy(old_images)
            new_images.append(self.soi_is.current_object)

        if command.cmd_type == CECommand.change_current_object:
            obj_name = command.cmd_args[0]
            self.soi_is.set_current_object(obj_name)
            new_images = copy(old_images)

        if command.cmd_type == CECommand.change_attrib_value:
            attr_name = command.cmd_args[0]
            print("Attr name = ", attr_name)
            new_attr_value = command.cmd_args[1]
            setattr(self.soi_is.current_object, attr_name, new_attr_value)
            if self.soi_is.curr_obj_is_new:
                new_images = copy(old_images)
                new_images.append(self.soi_is.current_object)
            else:
                new_images = self.soi_is.soi_objects

        try:
            self.model_building(new_images)
        except (DependenciesBuildError, AttributeEvaluateError) as e:
            self.attribute_error_handler(attr_name, e.args[0])
            self.model_building(old_images)

    def attribute_error_handler(self, attr_name: str, message: str):
        print("Attribute error! \nattr_name: {}\n message: {}".format(attr_name, message))

    def cut_slice(self, chain: CommandChain):
        self.command_chains = self.command_chains[:self.command_chains.index(chain)+1]

    def save_state(self):
        cc = CommandChain(Command(CECommand(CECommand.load_objects),
                                  [self.soi_is.copied_soi_objects]))
        self.command_chains.append(cc)
        self.command_pointer = cc.cmd_chain[-1]
        self.execute_commands()

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

            # if self.command_pointer.cmd_type == CECommand.load_objects:
            # elif self.command_pointer.cmd_type == CECommand.create_new_object:
            #     print("undo for create_new_object")

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

    """ High-level operations - by 'buttons' """

    def read_station_config(self, dir_name: str):
        self.soi_is.read_station_config(dir_name)
        self.save_state()

    def eval_routes(self, train_xml: str, shunt_xml: str):
        self.model.eval_routes(train_xml, shunt_xml)

    def create_new_object(self, cls_name: str):
        self.continue_commands(Command(CECommand(CECommand.create_new_object), [cls_name]))

    def change_current_object(self, name: str):
        self.continue_commands(Command(CECommand(CECommand.change_current_object), [name]))

    def change_attribute_value(self, attr_name: str, new_value: str):
        self.continue_commands(Command(CECommand(CECommand.change_attrib_value), [attr_name, new_value]))


# def execute_commands(commands: list[Command]):
#     for command in commands:
#         if command.cmd_type == CECommand.load_objects:
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
        # execute_commands([Command(CECompositeCommand(CECompositeCommand.load_objects), [STATION_IN_CONFIG_FOLDER])])
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
        print([command_chain.cmd_chain for command_chain in cmd_sup.command_chains])
        cmd_sup.eval_routes("TrainRoute.xml", "ShuntingRoute.xml")

    test_15 = False
    if test_15:
        cmd_sup = CommandSupervisor()
        cmd_sup.create_new_object("CoordinateSystemSOI")
        # cmd_sup.create_new_object("AxisSOI")
        # cmd_sup.create_new_object("LineSOI")
        curr_obj = cmd_sup.soi_is.current_object
        curr_obj.x = "5"
        print(curr_obj)
        print(curr_obj._str_x)
        cmd_sup.undo()
        curr_obj_after_undo = cmd_sup.soi_is.current_object
        print()
        print(curr_obj_after_undo)

    test_16 = False
    if test_16:
        cmd_sup = CommandSupervisor()
        cmd_sup.create_new_object("CoordinateSystemSOI")
        cmd_sup.change_attribute_value("x", "5")
        curr_obj = cmd_sup.soi_is.current_object
        print(curr_obj)
        print(curr_obj._str_x)

    test_17 = True
    if test_17:
        cmd_sup = CommandSupervisor()
        cmd_sup.create_new_object("CoordinateSystemSOI")
        print(cmd_sup.soi_is.current_object.__dict__)
        cmd_sup.change_attribute_value("name", "MyCS")
