from __future__ import annotations

from custom_enum import CustomEnum
from soi_interactive_storage import SOIInteractiveStorage
from mo_model_builder import ModelBuilder
from soi_objects import StationObjectImage

from config_names import STATION_IN_CONFIG_FOLDER


class CEElementaryCommand(CustomEnum):
    create_object = 0
    change_attrib_value = 1
    elementary_delete_object = 2


class CECompositeCommand(CustomEnum):
    load_config = 0
    create_object = 1
    rename_object = 2
    change_attrib_value = 3
    delete_object = 4


class Command:
    def __init__(self, cmd_type: CECompositeCommand, cmd_args: list[str]):
        """ Commands have next formats:
        load_config(file_name) (or dir_name)
        create_object(cls_name)
        rename_object(old_name, new_name)
        change_attrib_value(obj_name, attr_name, new_value)
        delete_object(obj_name)
        """
        self.cmd_type = cmd_type
        self.cmd_args = cmd_args


class CommandChain:
    def __init__(self, head: list[StationObjectImage] = None):
        if head is None:
            self.head = []
        else:
            self.head = head
        self.command_chain = []

    def append_command(self, command: Command):
        self.command_chain.append(command)

    def get_slice(self, command: Command):
        """ command included in list"""
        new_cc = CommandChain(self.head)
        new_cc.command_chain = self.command_chain[:self.command_chain.index(command)]
        return new_cc

    def command_in_chain(self, command: Command) -> int:
        if command not in self.command_chain:
            return -1
        return self.command_chain.index(command)

    # def remove_command(self):
    #     pass


class CommandSupervisor:
    def __init__(self):
        self.command_chains: list[CommandChain] = [CommandChain()]
        self.command_pointer = None

    def save_state(self, soi_is: SOIInteractiveStorage):
        self.command_chains.append(CommandChain(soi_is.copied_soi_objects))

    def append_command(self, command: Command):
        self.command_chains[-1].append_command(command)

    # def remove_command(self):
    #     pass

    def execute_command(self, command: Command):
        pass

    def execute_commands(self):
        last_command = False
        if self.command_pointer:
            for chain in self.command_chains:
                for command in chain.command_chain:
                    self.execute_command(command)
                    if command is self.command_pointer:
                        last_command = True
                        break
                if last_command:
                    break

    def undo(self):
        if self.command_pointer:
            for chain in self.command_chains:
                for command in chain.command_chain:
                    pass

    def redo(self):
        pass


def execute_commands(commands: list[Command]):
    for command in commands:
        if command.cmd_type == CECompositeCommand.load_config:
            dir_name = command.cmd_args[0]
            SOI_IS.read_station_config(dir_name)
            images = SOI_IS.soi_objects
            MODEL.build_dg(images)
            MODEL.evaluate_attributes()
            MODEL.build_skeleton()
            MODEL.eval_link_length()
            MODEL.build_lights()
            MODEL.build_rail_points()
            MODEL.build_borders()
            MODEL.build_sections()


SOI_IS = SOIInteractiveStorage()
MODEL = ModelBuilder()


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

    test_12 = True
    if test_12:
        execute_commands([Command(CECompositeCommand(CECompositeCommand.load_config), [STATION_IN_CONFIG_FOLDER])])
        MODEL.eval_routes("TrainRoute.xml", "ShuntingRoute.xml")
