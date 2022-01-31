from __future__ import annotations
from typing import Optional
from collections import OrderedDict, Counter
import math

from custom_enum import CustomEnum
from enums_images import CEAxisCreationMethod, CEAxisOrLine, CELightRouteType, CELightStickType, \
    CELightColor, CEBorderType, CESectionType
from soi_objects import StationObjectImage, CoordinateSystemSOI, AxisSOI, PointSOI, LineSOI, \
    LightSOI, RailPointSOI, BorderSOI, SectionSOI
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Route, NodeInterface
from cell_object import CellObject
from graphical_object import Point2D, Angle, Line2D, BoundedCurve, lines_intersection, evaluate_vector, \
    ParallelLinesException, EquivalentLinesException, PointsEqualException, OutBorderException
from cell_access_functions import NotFoundCellError, element_cell_by_type, all_cells_of_type, find_cell_name
from rail_route import RailRoute
from xml_formation import form_rail_routes_xml
from soi_files_handler import make_xlsx_templates, read_station_config
from soi_rectifier import SOIRectifier
from soi_attributes_evaluator import check_expected_type, default_attrib_evaluation, evaluate_attributes

from config_names import GLOBAL_CS_NAME, STATION_OUT_CONFIG_FOLDER, STATION_IN_CONFIG_FOLDER


# ------------        EXCEPTIONS        ------------ #

# ------------        MODEL BUILD EXCEPTIONS        ------------ #

class ModelBuildError(Exception):
    pass


class MBSkeletonError(ModelBuildError):
    pass


class MBEquipmentError(ModelBuildError):
    pass


# ------------        ATTRIBUTE EVALUATIONS EXCEPTIONS        ------------ #


# ------------        ENUMS        ------------ #


class CECommand(CustomEnum):
    load_config = 0
    create_object = 1
    rename_object = 2
    change_attrib_value = 3
    delete_object = 4


# -------------------------        MODEL GRAPH CELLS           -------------------- #


class PointCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class RailPointCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class BorderCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class LightCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class IsolatedSectionCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class LineCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class LengthCell(CellObject):
    def __init__(self, length: float):
        self.length = length


class RailPointDirectionCell(CellObject):
    def __init__(self, direction: str):
        self.direction = direction


# -------------------------        MODEL CLASSES           -------------------- #


class ModelObject:
    def __init__(self):
        self.name: str = ""


class CoordinateSystemMO(ModelObject):
    def __init__(self, base_cs: CoordinateSystemMO = None,
                 x: int = 0, co_x: bool = True, co_y: bool = True):
        super().__init__()
        self._base_cs = base_cs
        self._is_base = base_cs is None
        self._in_base_x = x
        self._in_base_co_x = co_x
        self._in_base_co_y = co_y

    @property
    def is_base(self) -> bool:
        return self._is_base

    @property
    def base_cs(self) -> CoordinateSystemMO:
        if self.is_base:
            return self
        return self._base_cs

    @property
    def in_base_x(self) -> int:
        return self._in_base_x

    @property
    def in_base_co_x(self) -> bool:
        return self._in_base_co_x

    @property
    def in_base_co_y(self) -> bool:
        return self._in_base_co_y

    @property
    def absolute_x(self) -> int:
        if self.is_base:
            return self.in_base_x
        return int(self.base_cs.absolute_x + self.in_base_x * (-0.5 + int(self.base_cs.absolute_co_x)) * 2)

    @property
    def absolute_co_x(self) -> bool:
        if self.is_base:
            return self.in_base_co_x
        return self.base_cs.absolute_co_x == self.in_base_co_x

    @property
    def absolute_co_y(self) -> bool:
        if self.is_base:
            return self.in_base_co_y
        return self.base_cs.absolute_co_y == self.in_base_co_y


class AxisMO(ModelObject):
    def __init__(self, line2D: Line2D):
        super().__init__()
        self.line2D = line2D
        self._points: list[PointMO] = []
        self._lines: list[LineMO] = []

    def append_point(self, point: PointMO):
        self._points.append(point)

    def append_line(self, line: LineMO):
        self._lines.append(line)

    @property
    def points(self):
        return sorted(self._points, key=lambda s: s.x)

    @property
    def lines(self):
        return self._lines

    @property
    def angle(self):
        return self.line2D.angle


class PointMO(ModelObject):
    def __init__(self, point2D: Point2D):
        super().__init__()
        self.point2D = point2D

    @property
    def x(self):
        return self.point2D.x

    @property
    def y(self):
        return self.point2D.y


class LineMO(ModelObject):
    def __init__(self, boundedCurves: list[BoundedCurve], points: list[PointMO] = None):
        super().__init__()
        self.boundedCurves = boundedCurves
        self._points: list[PointMO] = []
        self._axis = None
        if points:
            self._points = points

    def append_point(self, point: PointMO):
        self._points.append(point)

    @property
    def points(self):
        return sorted(self._points, key=lambda s: s.x)

    @property
    def min_point(self):
        assert len(self.points) >= 2, "Count of points <2"
        return self.points[0]

    @property
    def max_point(self):
        assert len(self.points) >= 2, "Count of points <2"
        return self.points[-1]

    @property
    def axis(self) -> AxisMO:
        return self._axis

    @axis.setter
    def axis(self, val: AxisMO):
        self._axis = val


class LightMO(ModelObject):
    def __init__(self, route_type: CELightRouteType, end_forward_tpl1: str,
                 colors: list[CELightColor], stick_type: CELightStickType):
        super().__init__()
        self.route_type = route_type
        self.end_forward_tpl1 = end_forward_tpl1
        self.colors = colors
        self.stick_type = stick_type


class RailPointMO(ModelObject):
    def __init__(self, end_tpl0: str):
        super().__init__()
        self.end_tpl0 = end_tpl0


class BorderMO(ModelObject):
    def __init__(self, border_type: CEBorderType, end_not_inf_tpl0: Optional[str] = None):
        super().__init__()
        self.border_type = border_type
        self.end_not_inf_tpl0 = end_not_inf_tpl0


class SectionMO(ModelObject):
    def __init__(self, section_type: CESectionType, rail_points_names: list[str] = None):
        super().__init__()
        self.section_type = section_type
        if not rail_points_names:
            self.rail_points_names = []
        else:
            self.rail_points_names = rail_points_names


GLOBAL_CS_MO = CoordinateSystemMO()
GLOBAL_CS_MO._name = GLOBAL_CS_NAME


class Command:
    def __init__(self, cmd_type: CECommand, cmd_args: list[str]):
        """ Commands have next formats:
        load_config(file_name) (or dir_name)
        create_object(cls_name)
        rename_object(old_name, new_name)
        change_attrib_value(obj_name, attr_name, new_value)
        delete_object(obj_name)
        """
        self.cmd_type = cmd_type
        self.cmd_args = cmd_args


class CommandSupervisor:
    def __init__(self):
        self.commands = []

    def add_command(self):
        pass

    def remove_command(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass


def execute_commands(commands: list[Command]):
    for command in commands:
        if command.cmd_type == CECommand.load_config:
            dir_name = command.cmd_args[0]
            images = read_station_config(dir_name)
            MODEL.build_dg(images)
            MODEL.evaluate_attributes()
            MODEL.build_skeleton()
            MODEL.eval_link_length()
            MODEL.build_lights()
            MODEL.build_rail_points()
            MODEL.build_borders()
            MODEL.build_sections()


class ModelBuilder:
    def __init__(self):
        self.rectifier = SOIRectifier()
        self.names_soi: OrderedDict[str, StationObjectImage] = OrderedDict()
        self.rect_so: list[str] = []

        self.names_mo: OrderedDict[str, OrderedDict[str, ModelObject]] = OrderedDict()  # cls_name: obj_name: obj
        self.refresh_storages()

        self.smg = OneComponentTwoSidedPG()

    def refresh_storages(self):
        self.rectifier.refresh_storages()
        self.names_mo: OrderedDict[str, OrderedDict[str, ModelObject]] = OrderedDict()
        self.names_mo["CoordinateSystem"]: OrderedDict[str, CoordinateSystemMO] = OrderedDict()
        self.names_mo["CoordinateSystem"][GLOBAL_CS_NAME] = GLOBAL_CS_MO
        self.rect_so: list[str] = []

    def build_dg(self, images: list[StationObjectImage]) -> None:
        self.refresh_storages()
        self.names_soi, self.rect_so = self.rectifier.rectification_results(images)

    def evaluate_attributes(self):
        self.names_soi = evaluate_attributes(self.names_soi, self.rect_so)

    def build_skeleton(self):

        if "CoordinateSystem" not in self.names_mo:
            self.names_mo["CoordinateSystem"] = OrderedDict()
        if "Axis" not in self.names_mo:
            self.names_mo["Axis"] = OrderedDict()
        if "Point" not in self.names_mo:
            self.names_mo["Point"] = OrderedDict()
        if "Line" not in self.names_mo:
            self.names_mo["Line"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, CoordinateSystemSOI):
                model_object = CoordinateSystemMO(self.names_mo["CoordinateSystem"][image.cs_relative_to.name],
                                                  image.x, image.co_x == "true", image.co_y == "true")
                model_object.name = image_name
                self.names_mo["CoordinateSystem"][image_name] = model_object

            if isinstance(image, AxisSOI):
                cs_rel: CoordinateSystemMO = self.names_mo["CoordinateSystem"][image.cs_relative_to.name]
                if image.creation_method == CEAxisCreationMethod.translational:
                    cs_rel_mo: CoordinateSystemMO = self.names_mo["CoordinateSystem"][image.cs_relative_to.name]
                    center_point_x = cs_rel.absolute_x
                    center_point_y = image.y * int(2*(int(cs_rel_mo.absolute_co_y)-0.5))
                    angle = 0
                else:
                    center_point_soi: PointSOI = image.center_point
                    center_point_mo: PointMO = self.names_mo["Point"][center_point_soi]
                    center_point_x = center_point_mo.x
                    center_point_y = center_point_mo.y
                    angle = image.alpha
                    if center_point_soi.on == CEAxisOrLine.line:
                        raise MBSkeletonError("Building axis by point on line is impossible")
                    if Angle(angle) == Angle(math.pi/2):
                        raise MBSkeletonError("Building vertical axis is impossible")
                line2D = Line2D(Point2D(center_point_x, center_point_y), angle=Angle(angle))

                model_object = AxisMO(line2D)
                model_object.name = image_name

                for model_object_2 in self.names_mo["Axis"].values():
                    model_object_2: AxisMO
                    try:
                        lines_intersection(model_object.line2D, model_object_2.line2D)
                    except ParallelLinesException:
                        continue
                    except EquivalentLinesException:
                        raise MBSkeletonError("Cannot re-build existing axis")

                if image.creation_method == CEAxisCreationMethod.rotational:
                    center_point_soi: PointSOI = image.center_point
                    model_object.append_point(center_point_soi)
                self.names_mo["Axis"][image_name] = model_object

            if isinstance(image, PointSOI):
                cs_rel: CoordinateSystemMO = self.names_mo["CoordinateSystem"][image.cs_relative_to.name]
                point_x = cs_rel.absolute_x + image.x * cs_rel.absolute_co_x
                if image.on == CEAxisOrLine.axis:
                    axis: AxisMO = self.names_mo["Axis"][image.axis.name]
                    pnt2D = lines_intersection(axis.line2D, Line2D(Point2D(point_x, 0), angle=Angle(math.pi / 2)))
                else:
                    line: LineMO = self.names_mo["Line"][image.line.name]
                    try:
                        pnt2D_y = line.boundedCurves[0].y_by_x(point_x)
                    except OutBorderException:
                        if len(line.boundedCurves) == 1:
                            raise MBSkeletonError("Point out of borders")
                        else:
                            try:
                                pnt2D_y = line.boundedCurves[1].y_by_x(point_x)
                            except OutBorderException:
                                raise MBSkeletonError("Point out of borders")
                    pnt2D = Point2D(point_x, pnt2D_y)

                model_object = PointMO(pnt2D)
                model_object.name = image_name

                for model_object_2 in self.names_mo["Point"].values():
                    model_object_2: PointMO
                    try:
                        evaluate_vector(model_object.point2D, model_object_2.point2D)
                    except PointsEqualException:
                        raise MBSkeletonError("Cannot re-build existing point")

                if image.on == CEAxisOrLine.axis:
                    axis: AxisMO = self.names_mo["Axis"][image.axis.name]
                    self.point_to_axis_handling(model_object, axis)
                else:
                    line: LineMO = self.names_mo["Line"][image.line.name]
                    self.point_to_line_handling(model_object, line)
                self.names_mo["Point"][image_name] = model_object

            if isinstance(image, LineSOI):
                points_so: list[PointSOI] = image.points
                points_mo: list[PointMO] = [self.names_mo["Point"][point.name] for point in points_so]
                point_1, point_2 = points_mo[0], points_mo[1]
                axises_mo: list[AxisMO] = []
                for point_so in points_so:
                    if point_so.on == CEAxisOrLine.line:
                        line_mo: LineMO = self.names_mo["Line"][point_so.line.name]
                        if not line_mo.axis:
                            raise MBSkeletonError("Cannot build line by point on line")
                        axises_mo.append(line_mo.axis)
                    else:
                        axis_mo: AxisMO = self.names_mo["Axis"][point_so.axis.name]
                        axises_mo.append(axis_mo)
                axis_1, axis_2 = axises_mo[0], axises_mo[1]
                if axis_1 is axis_2:
                    boundedCurves = [BoundedCurve(point_1.point2D, point_2.point2D)]
                elif axis_1.angle == axis_2.angle:
                    center_point = Point2D(0.5*(point_1.point2D.x+point_2.point2D.x),
                                           0.5*(point_1.point2D.y+point_2.point2D.y))
                    boundedCurves = [BoundedCurve(point_1.point2D, center_point, axis_1.angle),
                                     BoundedCurve(point_2.point2D, center_point, axis_2.angle)]
                else:
                    boundedCurves = [BoundedCurve(point_1.point2D, point_2.point2D, axis_1.angle, axis_2.angle)]
                model_object = LineMO(boundedCurves)
                model_object.name = image_name

                model_object.append_point(point_1)
                model_object.append_point(point_2)
                if axis_1 is axis_2:
                    self.line_to_axis_handling(model_object, axis_1)
                else:
                    self.line_connection_handling(point_1, point_2)
                self.names_mo["Line"][image_name] = model_object

    def point_to_line_handling(self, point: PointMO, line: LineMO):
        old_points = line.points
        prev_point, next_point = None, None
        place_found = False
        for i_ in range(len(old_points)-1):
            if old_points[i_].x < point.x < old_points[i_+1].x:
                place_found = True
                prev_point, next_point = old_points[i_], old_points[i_+1]
        assert place_found, "point before inserting not found"
        assert next_point, "end of point list"

        prev_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, PointCell, prev_point.name)[1]
        next_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, PointCell, next_point.name)[1]

        new_point_node = self.smg.insert_node(next_node.ni_nd, prev_node.ni_pu)
        new_point_node.append_cell_obj(PointCell(point.name))

        line.append_point(point)

    def point_to_axis_handling(self, point: PointMO, axis: AxisMO):
        lines = axis.lines
        for line in lines:
            if line.min_point.x < point.x < line.max_point.x:
                self.point_to_line_handling(point, line)
                break

        axis.append_point(point)

    def line_connection_handling(self, pnt_1: PointMO, pnt_2: PointMO):
        min_point, max_point = (pnt_1, pnt_2) if (pnt_1.x < pnt_2.x) else (pnt_2, pnt_1)

        try:

            min_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, PointCell, min_point.name)[1]
        except NotFoundCellError:
            min_node = self.smg.insert_node()
            min_node.append_cell_obj(PointCell(min_point.name))

        try:
            max_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, PointCell, max_point.name)[1]
        except NotFoundCellError:
            max_node = self.smg.insert_node()
            max_node.append_cell_obj(PointCell(max_point.name))

        self.smg.connect_inf_handling(min_node.ni_pu, max_node.ni_nd)

    def line_to_axis_handling(self, line: LineMO, axis: AxisMO):
        old_lines = axis.lines
        axis_points = axis.points
        for old_line in old_lines:
            if (line.min_point.x > old_line.max_point.x) or (old_line.min_point.x > line.max_point.x):
                continue
            else:
                raise MBSkeletonError("lines intersection on axis found")
        on_line_points = axis_points[axis_points.index(line.min_point):axis_points.index(line.max_point)+1]
        last_nd_interface = self.smg.inf_pu.ni_nd
        for line_point in reversed(on_line_points):
            try:
                point_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, PointCell, line_point.name)[1]
                self.smg.connect_inf_handling(last_nd_interface, point_node.ni_pu)
            except NotFoundCellError:
                point_node = self.smg.insert_node(last_nd_interface)
                point_node.append_cell_obj(PointCell(line_point.name))
            last_nd_interface = point_node.ni_nd

        axis.append_line(line)
        line.axis = axis

    def eval_link_length(self):
        for link in self.smg.not_inf_links:
            pn_s_ = [ni.pn for ni in link.ni_s]
            pnt_cells_: list[PointCell] = [element_cell_by_type(pn, PointCell) for pn in pn_s_]
            link.append_cell_obj(LengthCell(abs(self.names_mo["Point"][pnt_cells_[0].name].x -
                                                self.names_mo["Point"][pnt_cells_[1].name].x)))

    def build_lights(self):

        if "Light" not in self.names_mo:
            self.names_mo["Light"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, LightSOI):
                center_point: PointMO = self.names_mo["Point"][image.center_point.name]
                direct_point: PointMO = self.names_mo["Point"][image.direct_point.name]

                if center_point is direct_point:
                    raise MBEquipmentError("Direction point is equal to central point")

                # check direction
                center_point_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, PointCell, center_point.name)[1]
                direct_point_node = find_cell_name(self.smg.not_inf_nodes, PointCell, direct_point.name)[1]
                routes_node_to_node = self.smg.routes_node_to_node(center_point_node, direct_point_node)
                if not routes_node_to_node:
                    raise MBEquipmentError("Route from central point to direction point not found")

                model_object = LightMO(image.light_route_type, routes_node_to_node[1].end_str,
                                       image.colors, image.light_stick_type)
                center_point_node.append_cell_obj(LightCell(image_name))

                model_object.name = image_name
                self.names_mo["Light"][image_name] = model_object

    def build_rail_points(self):

        if "RailPoint" not in self.names_mo:
            self.names_mo["RailPoint"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, RailPointSOI):
                center_point: PointMO = self.names_mo["Point"][image.center_point.name]
                plus_point: PointMO = self.names_mo["Point"][image.dir_plus_point.name]
                minus_point: PointMO = self.names_mo["Point"][image.dir_minus_point.name]

                # check direction
                center_point_node = find_cell_name(self.smg.not_inf_nodes, PointCell, center_point.name)[1]
                plus_point_node = find_cell_name(self.smg.not_inf_nodes, PointCell, plus_point.name)[1]
                minus_point_node = find_cell_name(self.smg.not_inf_nodes, PointCell, minus_point.name)[1]
                plus_routes, ni_plus = self.smg.routes_node_to_node(center_point_node, plus_point_node)
                minus_routes, ni_minus = self.smg.routes_node_to_node(center_point_node, minus_point_node)
                if not plus_routes:
                    raise MBEquipmentError("Route from central point to '+' point not found")
                if not minus_routes:
                    raise MBEquipmentError("Route from central point to '-' point not found")
                for plus_route in plus_routes:
                    for minus_route in minus_routes:
                        if plus_route.partially_overlaps(minus_route):
                            raise MBEquipmentError("Cannot understand '+' and '-' directions because their overlaps")
                if not (ni_plus is ni_minus):
                    raise MBEquipmentError("Defined '+' or '-' direction is equal to 0-direction")

                # + and - move cells
                plus_route = plus_routes[0]
                plus_link = plus_route.links[0]
                plus_move = ni_plus.get_move_by_link(plus_link)
                plus_move.append_cell_obj(RailPointDirectionCell("+{}".format(image.name)))
                minus_route = minus_routes[0]
                minus_link = minus_route.links[0]
                minus_move = ni_minus.get_move_by_link(minus_link)
                minus_move.append_cell_obj(RailPointDirectionCell("-{}".format(image.name)))

                model_object = RailPointMO(ni_plus.pn.opposite_ni(ni_plus).end_str)
                center_point_node.append_cell_obj(RailPointCell(image_name))
                model_object.name = image_name
                self.names_mo["RailPoint"][image_name] = model_object

    def build_borders(self):

        if "Border" not in self.names_mo:
            self.names_mo["Border"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, BorderSOI):
                point_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, PointCell, image.point.name)[1]
                inf_ni_str = None
                if point_node in self.smg.nodes_inf_connected:
                    inf_ni_str = self.smg.nodes_inf_connected[point_node].opposite_end_str

                model_object = BorderMO(image.border_type, inf_ni_str)
                point_node.append_cell_obj(BorderCell(image_name))
                model_object.name = image_name
                self.names_mo["Border"][image_name] = model_object

    def build_sections(self):

        if "Section" not in self.names_mo:
            self.names_mo["Section"] = OrderedDict()

        for image_name in self.rect_so:
            image = self.names_soi[image_name]

            if isinstance(image, SectionSOI):
                border_points: list[PointMO] = [self.names_mo["Point"][point.name] for point in image.border_points]
                point_nodes: list[PolarNode] = [find_cell_name(self.smg.not_inf_nodes, PointCell, point.name)[1]
                                                for point in border_points]
                closed_links, closed_nodes = self.smg.closed_links_nodes(point_nodes)
                if not closed_links:
                    raise MBEquipmentError("No closed links found")

                # check links sections and make cells
                for link in closed_links:
                    try:
                        element_cell_by_type(link, IsolatedSectionCell)
                    except NotFoundCellError:
                        pass
                    else:
                        raise MBEquipmentError("Section in link already exists")
                    link.append_cell_obj(IsolatedSectionCell(image.name))

                # section type and rail points evaluations
                rail_points = []
                if len(closed_links) > 1:
                    section_type = CESectionType(CESectionType.non_stop)
                    for node in closed_nodes:
                        try:
                            rail_cell: RailPointCell = element_cell_by_type(node, RailPointCell)
                        except NotFoundCellError:
                            continue
                        rail_points.append(rail_cell.name)
                else:
                    link = closed_links.pop()
                    light_names: dict[str, NodeInterface] = {}
                    for ni in link.ni_s:
                        node = ni.pn
                        try:
                            light_cell: LightCell = element_cell_by_type(node, LightCell)
                        except NotFoundCellError:
                            continue
                        light_names[light_cell.name] = ni
                    if not light_names:
                        raise MBEquipmentError("Found segment section |-----| with 0 border lights")
                    if len(light_names) == 2:
                        section_type = CESectionType(CESectionType.shunt_stop)
                        for light_name in light_names:
                            light: LightMO = self.names_mo['Light'][light_name]
                            link_ni = light_names[light_name]
                            if (light.route_type == CELightRouteType.train) and (link_ni.end != light.end_forward_tpl1):
                                section_type = CESectionType(CESectionType.track)
                                break
                    else:
                        section_type = CESectionType(CESectionType.indic)

                model_object = SectionMO(section_type, rail_points)
                model_object.name = image_name
                self.names_mo["Section"][image_name] = model_object

    def eval_routes(self, train_routes_file_name, shunting_routes_file_name):

        train_light_routes_dict: OrderedDict[str, tuple[list[RailRoute], list[RailRoute]]] = OrderedDict()
        shunting_light_routes_dict: OrderedDict[str, list[RailRoute]] = OrderedDict()

        route_id = 1

        # 1. Form routes from smg
        light_cells_: dict[LightCell, PolarNode] = all_cells_of_type(self.smg.not_inf_nodes, LightCell)
        for light_cell in light_cells_:
            light: LightMO = self.names_mo["Light"][light_cell.name]
            start_ni = light_cells_[light_cell].ni_by_end(light.end_forward_tpl1)
            routes = self.smg.walk(start_ni)
            train_route_slices: list[Route] = []
            shunting_route_slices: list[Route] = []

            # 1.0 Is enter signal check
            is_enter_signal = False
            if light.route_type == CELightRouteType.train:
                try:
                    element_cell_by_type(start_ni.pn, BorderCell)
                except NotFoundCellError:
                    pass
                else:
                    is_enter_signal = True

            # 1.1 Slices extraction
            for route in routes:

                # 1.1.1 Train routes slices extraction
                if light.route_type == CELightRouteType.train:

                    train_slice_repeats = False
                    not_possible_end_train = False
                    train_route_slice = None
                    for ni in route.outer_ni_s[1:]:
                        node = ni.pn

                        # 1.1.1.1 Check if node is light
                        light_cell = None
                        try:
                            light_cell: LightCell = element_cell_by_type(node, LightCell)
                        except NotFoundCellError:
                            pass
                        if light_cell:
                            light_found: LightMO = self.names_mo["Light"][light_cell.name]
                            if ni.end == light_found.end_forward_tpl1:
                                if light_found.route_type == CELightRouteType.train:
                                    train_route_slice = route.get_slice(route.start_ni, ni.pn.opposite_ni(ni))
                                    for old_train_route_slice in train_route_slices:
                                        if old_train_route_slice == train_route_slice:
                                            train_slice_repeats = True
                                            break
                                    break

                        # 1.1.1.2 Check if node is border
                        border_cell = None
                        try:
                            border_cell: BorderCell = element_cell_by_type(node, BorderCell)
                        except NotFoundCellError:
                            pass
                        if border_cell:
                            border_found: BorderMO = self.names_mo["Border"][border_cell.name]
                            if (light.route_type == CELightRouteType.train) and\
                               (border_found.border_type == CEBorderType.standoff):
                                not_possible_end_train = True
                                break
                            train_route_slice = route.get_slice(route.start_ni, ni.pn.opposite_ni(ni))
                            for old_route_slice in train_route_slices:
                                if old_route_slice == train_route_slice:
                                    train_slice_repeats = True
                                    break
                            break

                    if (not train_slice_repeats) and (not not_possible_end_train) and train_route_slice:
                        train_route_slices.append(train_route_slice)

                # 1.1.2 Shunting routes slices extraction
                if not is_enter_signal:
                    shunting_slice_repeats = False
                    shunting_route_slice = None
                    for ni in route.outer_ni_s[1:]:
                        node = ni.pn

                        # 1.1.2.1 Check if node is light
                        light_cell = None
                        try:
                            light_cell: LightCell = element_cell_by_type(node, LightCell)
                        except NotFoundCellError:
                            pass
                        if light_cell:
                            light_found: LightMO = self.names_mo["Light"][light_cell.name]
                            if ni.end == light_found.end_forward_tpl1:
                                shunting_route_slice = route.get_slice(route.start_ni, ni.pn.opposite_ni(ni))
                                for old_shunting_route_slice in shunting_route_slices:
                                    if old_shunting_route_slice == shunting_route_slice:
                                        shunting_slice_repeats = True
                                        break
                                break

                        # 1.1.2.2 Check if node is border
                        border_cell = None
                        try:
                            border_cell: BorderCell = element_cell_by_type(node, BorderCell)
                        except NotFoundCellError:
                            pass
                        if border_cell:
                            shunting_route_slice = route.get_slice(route.start_ni, ni.pn.opposite_ni(ni))
                            for old_shunting_route_slice in shunting_route_slices:
                                if old_shunting_route_slice == shunting_route_slice:
                                    shunting_slice_repeats = True
                                    break
                            break

                    if (not shunting_slice_repeats) and shunting_route_slice:
                        shunting_route_slices.append(shunting_route_slice)

            # 1.2 Route info extraction
            train_routes = []
            shunting_routes = []

            for train_route_slice in train_route_slices:
                train_route = RailRoute(route_id)

                # route_type
                train_route.route_type = "PpoTrainRoute"

                # tag_end_eval
                end_node = train_route_slice.nodes[-1]
                light_cell: LightCell = element_cell_by_type(end_node, LightCell)
                end_light_name = light_cell.name
                train_route.route_tag = "{}_{}".format(light.name, end_light_name)

                # trace_begin
                train_route.trace_begin = light.name

                # trace_points
                trace_point_directions = []
                for link in train_route_slice.links:
                    for ni in link.ni_s:
                        move_ = ni.get_move_by_link(link)
                        try:
                            rpdc_: RailPointDirectionCell = element_cell_by_type(move_, RailPointDirectionCell)
                        except NotFoundCellError:
                            pass
                        else:
                            trace_point_directions.append(rpdc_.direction)
                train_route.trace_points = " ".join(trace_point_directions)

                # trace_end
                try:
                    border_cell: BorderCell = element_cell_by_type(end_node, BorderCell)
                    trace_end = border_cell.name
                except NotFoundCellError:
                    trace_end = element_cell_by_type(end_node, LightCell).name
                train_route.trace_end = trace_end

                # finish_selectors
                end_link = train_route_slice.links[-1]
                end_section_cell: IsolatedSectionCell = element_cell_by_type(end_link, IsolatedSectionCell)
                end_section: SectionMO = self.names_mo["Section"][end_section_cell.name]
                finish_selectors = [end_light_name]
                if end_section.section_type == CESectionType.track:
                    node_before_end = train_route_slice.nodes[-2]
                    before_end_light_cell: LightCell = element_cell_by_type(node_before_end, LightCell)
                    finish_selectors.append(before_end_light_cell.name)
                train_route.end_selectors = " ".join(finish_selectors)

                route_id += 1
                train_routes.append(train_route)

            for shunting_route_slice in shunting_route_slices:
                shunting_route = RailRoute(route_id)

                # route_type
                shunting_route.route_type = "PpoShuntingRoute"

                # tag_end_eval
                end_node = shunting_route_slice.nodes[-1]
                try:
                    element_cell_by_type(end_node, BorderCell)  # border_cell: BorderCell =
                except NotFoundCellError:
                    end_light: LightCell = element_cell_by_type(end_node, LightCell)
                    end_light_name = end_light.name
                else:
                    before_end_node = shunting_route_slice.nodes[-2]
                    light_before_end_cell: LightCell = element_cell_by_type(before_end_node, LightCell)
                    end_light_name = light_before_end_cell.name

                shunting_route.route_tag = "{}_{}".format(light.name, end_light_name)

                # trace_begin
                shunting_route.trace_begin = light.name

                # trace_points
                trace_point_directions = []
                for link in shunting_route_slice.links:
                    for ni in link.ni_s:
                        move_ = ni.get_move_by_link(link)
                        try:
                            rpdc_: RailPointDirectionCell = element_cell_by_type(move_, RailPointDirectionCell)
                        except NotFoundCellError:
                            pass
                        else:
                            trace_point_directions.append(rpdc_.direction)
                shunting_route.trace_points = " ".join(trace_point_directions)

                # trace_end
                end_link = shunting_route_slice.links[-1]
                end_section_cell: IsolatedSectionCell = element_cell_by_type(end_link, IsolatedSectionCell)
                end_section: SectionMO = self.names_mo["Section"][end_section_cell.name]
                try:
                    border_cell: BorderCell = element_cell_by_type(end_node, BorderCell)
                except NotFoundCellError:
                    trace_end = element_cell_by_type(end_node, LightCell).name
                else:
                    if (end_section.section_type == CESectionType.indic) or \
                            (end_section.section_type == CESectionType.shunt_stop):
                        trace_end = end_section.name
                    else:
                        trace_end = border_cell.name

                shunting_route.trace_end = trace_end

                # finish_selectors
                finish_selectors = [end_light_name]
                if (end_section.section_type == CESectionType.track) or\
                        (end_section.section_type == CESectionType.shunt_stop):
                    node_before_end = shunting_route_slice.nodes[-2]
                    before_end_light_cell: LightCell = element_cell_by_type(node_before_end, LightCell)
                    if before_end_light_cell.name not in finish_selectors:
                        finish_selectors.append(before_end_light_cell.name)
                shunting_route.end_selectors = " ".join(finish_selectors)

                route_id += 1
                shunting_routes.append(shunting_route)

            if light.route_type == CELightRouteType.train:
                train_light_routes_dict[light.name] = (train_routes, shunting_routes)
            else:
                shunting_light_routes_dict[light.name] = shunting_routes

        # 2. Xml formation
        form_rail_routes_xml(train_light_routes_dict, shunting_light_routes_dict, "eval_results",
                             train_routes_file_name, shunting_routes_file_name)


MODEL = ModelBuilder()


if __name__ == "__main__":

    test_3 = False
    if test_3:
        pnt = PointSOI()
        pnt.x = "PK_12+34"
        print(type(pnt.x))
        print(pnt.x)
        print(PointSOI.attr_sequence_template)

    test_4 = False
    if test_4:
        cs = CoordinateSystemSOI()
        print(CoordinateSystemSOI.dict_possible_values)
        print(cs.dict_possible_values)

    test_5 = False
    if test_5:
        make_xlsx_templates(STATION_OUT_CONFIG_FOLDER)

    test_6 = False
    if test_6:
        objs = read_station_config(STATION_IN_CONFIG_FOLDER)
        # pnt = get_object_by_name("Point_15", objs)
        print(pnt.dict_possible_values)
        print(pnt.__class__.dict_possible_values)
        # for attr_ in pnt.active_attrs:
        #     print(getattr(pnt, attr_))

    test_7 = False
    if test_7:
        pnt = PointSOI()
        pnt.x = "PK_12+34"
        print(pnt.x)

    test_8 = False
    if test_8:
        objs = read_station_config(STATION_IN_CONFIG_FOLDER)
        # SOIR.build_dg(objs)
        # SOIR.check_cycle()
        # print([obj.name for obj in SOIR.rectified_object_list()])
        # build_model(SOIR.rectified_object_list())

    test_9 = False
    if test_9:
        execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
        print(MODEL.names_soi)
        print(MODEL.names_mo)

        # cs_1: CoordinateSystemMO = MODEL.names_mo['CS_1']
        # print(cs_1.absolute_x)
        # print(cs_1.absolute_y)
        # print(cs_1.absolute_co_x)
        # print(cs_1.absolute_co_y)
        # if 'CS_2' in MODEL.names_mo:
        #     cs_2 = MODEL.names_mo['CS_2']
        #     print(cs_2.absolute_x)
        #     print(cs_2.absolute_y)
        #     print(cs_2.absolute_co_x)
        #     print(cs_2.absolute_co_y)
        # if 'CS_3' in MODEL.names_mo:
        #     cs_3 = MODEL.names_mo['CS_3']
        #     print(cs_3.absolute_x)
        #     print(cs_3.absolute_y)
        #     print(cs_3.absolute_co_x)
        #     print(cs_3.absolute_co_y)

        ax_1: AxisMO = MODEL.names_mo['Axis_1']
        print(ax_1.line2D)

        line_2: LineMO = MODEL.names_mo['Line_7']
        print(line_2.boundedCurves)

        # pnt_15: PointMO = MODEL.names_mo['Axis_1']
        # print(ax_1.line2D)

    test_10 = False
    if test_10:

        execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
        print(MODEL.names_soi)
        # print(MODEL.names_soi.keys())  # .rect_so
        print(MODEL.rect_so)
        print(MODEL.names_mo)

        # line_1_node = get_point_node_DG("Line_1")
        # line_6_node = get_point_node_DG("Line_6")
        # point_16_node = get_point_node_DG("Point_16")
        # print("line_1_node", line_1_node)
        # print("line_6_node", line_6_node)
        # print("line_6 up connections", [link.opposite_ni(line_6_node.ni_pu).pn for link in line_6_node.ni_pu.links])
        # print("point_16_node", point_16_node)
        # print("point_16 up connections", [link.opposite_ni(point_16_node.ni_pu).pn for link in point_16_node.ni_pu.links])
        #
        # print(MODEL.dg.longest_coverage())
        # print("len routes", len(MODEL.dg.walk(MODEL.dg.inf_pu.ni_nd)))
        # i=0
        # for route in MODEL.dg.walk(MODEL.dg.inf_pu.ni_nd):
        #     if (line_6_node in route.nodes) or (line_6_node in route.nodes):
        #         i+=1
        #         print("i=", i)
        #         print("nodes", route.nodes)

        # ax_1: AxisMO = MODEL.names_mo['Axis_2']
        # print([pnt.x for pnt in ax_1.points])
        print(len(MODEL.smg.not_inf_nodes))

        print("minus inf", MODEL.smg.inf_nd)
        print("plus inf", MODEL.smg.inf_pu)
        for i in range(20):
            try:
                pnt_name = "Point_{}".format(str(i+1))
                pnt_node: PolarNode = find_cell_name(MODEL.smg.not_inf_nodes, PointCell, pnt_name)[1]
                print(pnt_name+" =>", pnt_node)
                print("nd-connections", [link.opposite_ni(pnt_node.ni_nd).pn for link in pnt_node.ni_nd.links])
                print("pu-connections", [link.opposite_ni(pnt_node.ni_pu).pn for link in pnt_node.ni_pu.links])
            except NotFoundCellError:
                continue
        print("len of links", len(MODEL.smg.links))
        for link in MODEL.smg.not_inf_links:
            print()
            ni_s = link.ni_s
            pn_s = [ni.pn for ni in link.ni_s]
            pnt_cells: list[PointCell] = [element_cell_by_type(pn, PointCell) for pn in pn_s]
            print("link between {}, {}".format(pnt_cells[0].name, pnt_cells[1].name))
            print("length {}".format(element_cell_by_type(link, LengthCell).length))
            for ni in ni_s:
                move = ni.get_move_by_link(link)
                if move.cell_objs:
                    rpdc = element_cell_by_type(move, RailPointDirectionCell)
                    print("Rail point direction = ", rpdc.direction)
            print("section {}".format(element_cell_by_type(link, IsolatedSectionCell).name))

    test_11 = False
    if test_11:
        execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
        light_cells = all_cells_of_type(MODEL.smg.not_inf_nodes, LightCell)
        print(len(light_cells))

    test_12 = True
    if test_12:
        execute_commands([Command(CECommand(CECommand.load_config), [STATION_IN_CONFIG_FOLDER])])
        MODEL.eval_routes("TrainRoute.xml", "ShuntingRoute.xml")
