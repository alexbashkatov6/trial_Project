from __future__ import annotations
from collections import OrderedDict
import math

from enums_images import CEAxisCreationMethod, CEAxisOrLine, CELightRouteType, CEBorderType, CESectionType
from soi_objects import StationObjectImage, CoordinateSystemSOI, AxisSOI, PointSOI, LineSOI, \
    LightSOI, RailPointSOI, BorderSOI, SectionSOI
from two_sided_graph import OneComponentTwoSidedPG, PolarNode, Route, NodeInterface
from cell_object import CellObject
from graphical_object import Point2D, Angle, Line2D, BoundedCurve, lines_intersection, evaluate_vector, \
    ParallelLinesException, EquivalentLinesException, PointsEqualException, OutBorderException
from cell_access_functions import NotFoundCellError, element_cell_by_type, all_cells_of_type, find_cell_name
from rail_route import RailRoute
from xml_formation import form_rail_routes_xml
from mo_objects import ModelObject, CoordinateSystemMO, AxisMO, PointMO, LineMO, LightMO, RailPointMO, BorderMO, \
    SectionMO
from default_ordered_dict import DefaultOrderedDict
from attribute_data import AttributeErrorData

from config_names import GLOBAL_CS_NAME


class ModelBuildError(Exception):
    pass


class MBSkeletonError(ModelBuildError):
    pass


class MBEquipmentError(ModelBuildError):
    pass


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


class ModelBuilder:
    def __init__(self):
        # gcs init
        self.mo_gcs = CoordinateSystemMO()
        self.mo_gcs.name = GLOBAL_CS_NAME

        self.reset_storages()

    def init_soi_list(self, images: list[StationObjectImage]):
        self.reset_storages()
        self.images = images

    def reset_storages(self):
        self.images: list[StationObjectImage] = []
        self.names_mo: DefaultOrderedDict[str, OrderedDict[str, ModelObject]] = DefaultOrderedDict(OrderedDict)
        self.names_mo["CoordinateSystem"][GLOBAL_CS_NAME] = self.mo_gcs
        self.smg = OneComponentTwoSidedPG()

    def build_skeleton(self):

        for image in self.images:
            # print("build", image)
            # print(type(image))
            image_name = image.name
            cls_name = image.__class__.__name__
            obj_name = image_name

            if isinstance(image, CoordinateSystemSOI):
                # print("CoordinateSystemSOI")
                model_object = CoordinateSystemMO(self.names_mo["CoordinateSystem"][
                                                      image.attr_confirmed_value("cs_relative_to").name],
                                                  image.attr_confirmed_value("x"),
                                                  image.attr_confirmed_value("co_x") == "true",
                                                  image.attr_confirmed_value("co_y") == "true")
                model_object.name = image_name
                self.names_mo["CoordinateSystem"][image_name] = model_object

            if isinstance(image, AxisSOI):
                cs_rel: CoordinateSystemMO = self.names_mo["CoordinateSystem"][
                                                      image.attr_confirmed_value("cs_relative_to").name]
                if image.attr_confirmed_value("creation_method") == "translational":
                    cs_rel_mo: CoordinateSystemMO = self.names_mo["CoordinateSystem"][image.attr_confirmed_value("cs_relative_to").name]
                    center_point_x = cs_rel.absolute_x
                    center_point_y = image.attr_confirmed_value("y") * int(2 * (int(cs_rel_mo.absolute_co_y) - 0.5))
                    angle = 0
                else:
                    center_point_soi: PointSOI = image.attr_confirmed_value("center_point")
                    # print("center_point_soi", center_point_soi)
                    center_point_mo: PointMO = self.names_mo["Point"][center_point_soi]
                    center_point_x = center_point_mo.x
                    center_point_y = center_point_mo.y
                    angle = image.attr_confirmed_value("alpha")
                    if center_point_soi.attr_confirmed_value("on") == "line":
                        raise MBSkeletonError("Building axis by point on line is impossible",
                                              AttributeErrorData(cls_name, obj_name, "center_point"))
                    if Angle(angle) == Angle(math.pi/2):
                        raise MBSkeletonError("Building vertical axis is impossible",
                                              AttributeErrorData(cls_name, obj_name, "alpha"))
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
                        raise MBSkeletonError("Cannot re-build existing axis",
                                              AttributeErrorData(cls_name, obj_name, ""))

                if image.attr_confirmed_value("creation_method") == "rotational":
                    center_point_soi: PointSOI = image.attr_confirmed_value("center_point")
                    model_object.append_point(center_point_soi)
                self.names_mo["Axis"][image_name] = model_object

            if isinstance(image, PointSOI):
                cs_rel: CoordinateSystemMO = self.names_mo["CoordinateSystem"][image.attr_confirmed_value("cs_relative_to").name]
                point_x = cs_rel.absolute_x + image.attr_confirmed_value("x") * cs_rel.absolute_co_x
                if image.attr_confirmed_value("on") == "axis":
                    axis: AxisMO = self.names_mo["Axis"][image.attr_confirmed_value("axis").name]
                    pnt2D = lines_intersection(axis.line2D, Line2D(Point2D(point_x, 0), angle=Angle(math.pi / 2)))
                else:
                    line: LineMO = self.names_mo["Line"][image.attr_confirmed_value("line").name]
                    try:
                        pnt2D_y = line.boundedCurves[0].y_by_x(point_x)
                    except OutBorderException:
                        if len(line.boundedCurves) == 1:
                            raise MBSkeletonError("Point out of borders", AttributeErrorData(cls_name, obj_name, "x"))
                        else:
                            try:
                                pnt2D_y = line.boundedCurves[1].y_by_x(point_x)
                            except OutBorderException:
                                raise MBSkeletonError("Point out of borders", AttributeErrorData(cls_name, obj_name, "x"))
                    pnt2D = Point2D(point_x, pnt2D_y)

                model_object = PointMO(pnt2D)
                model_object.name = image_name

                for model_object_2 in self.names_mo["Point"].values():
                    model_object_2: PointMO
                    try:
                        evaluate_vector(model_object.point2D, model_object_2.point2D)
                    except PointsEqualException:
                        raise MBSkeletonError("Cannot re-build existing point", AttributeErrorData(cls_name, obj_name, ""))

                if image.attr_confirmed_value("on") == "axis":
                    axis: AxisMO = self.names_mo["Axis"][image.attr_confirmed_value("axis").name]
                    self.point_to_axis_handling(model_object, axis)
                else:
                    line: LineMO = self.names_mo["Line"][image.attr_confirmed_value("line").name]
                    self.point_to_line_handling(model_object, line)
                self.names_mo["Point"][image_name] = model_object

            if isinstance(image, LineSOI):
                points_so: list[PointSOI] = image.attr_confirmed_value("points")
                points_mo: list[PointMO] = [self.names_mo["Point"][point.name] for point in points_so]
                if len(points_mo) != 2:
                    raise MBSkeletonError("Count of points should be == 2", AttributeErrorData(cls_name, obj_name, "points"))
                point_1, point_2 = points_mo[0], points_mo[1]
                axises_mo: list[AxisMO] = []
                for i, point_so in enumerate(points_so):
                    if point_so.attr_confirmed_value("on") == "line":
                        line_mo: LineMO = self.names_mo["Line"][point_so.attr_confirmed_value("line").name]
                        if not line_mo.axis:
                            raise MBSkeletonError("Cannot build line by point on line",
                                                  AttributeErrorData(cls_name, obj_name, "points", i))
                        axises_mo.append(line_mo.axis)
                    else:
                        axis_mo: AxisMO = self.names_mo["Axis"][point_so.attr_confirmed_value("axis").name]
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
                raise MBSkeletonError("Lines intersection on axis found",
                                      AttributeErrorData("Line", old_line.name, "points"))
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

        for image in self.images:
            image_name = image.name
            cls_name = image.__class__.__name__
            obj_name = image_name

            if isinstance(image, LightSOI):
                center_point: PointMO = self.names_mo["Point"][image.attr_confirmed_value("center_point").name]
                direct_point: PointMO = self.names_mo["Point"][image.attr_confirmed_value("direct_point").name]

                if center_point is direct_point:
                    raise MBEquipmentError("Direction point is equal to central point",
                                           AttributeErrorData(cls_name, obj_name, "direct_point"))

                # check direction
                center_point_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, PointCell, center_point.name)[1]
                direct_point_node = find_cell_name(self.smg.not_inf_nodes, PointCell, direct_point.name)[1]
                routes_node_to_node = self.smg.routes_node_to_node(center_point_node, direct_point_node)
                if not routes_node_to_node:
                    raise MBEquipmentError("Route from central point to direction point not found",
                                           AttributeErrorData(cls_name, obj_name, "direct_point"))

                model_object = LightMO(image.attr_confirmed_value("light_route_type"), routes_node_to_node[1].end_str,
                                       image.attr_confirmed_value("colors"), image.attr_confirmed_value("light_stick_type"))
                center_point_node.append_cell_obj(LightCell(image_name))

                model_object.name = image_name
                self.names_mo["Light"][image_name] = model_object

    def build_rail_points(self):

        for image in self.images:
            image_name = image.name
            cls_name = image.__class__.__name__
            obj_name = image_name

            if isinstance(image, RailPointSOI):
                center_point: PointMO = self.names_mo["Point"][image.attr_confirmed_value("center_point").name]
                plus_point: PointMO = self.names_mo["Point"][image.attr_confirmed_value("dir_plus_point").name]
                minus_point: PointMO = self.names_mo["Point"][image.attr_confirmed_value("dir_minus_point").name]

                # check direction
                center_point_node = find_cell_name(self.smg.not_inf_nodes, PointCell, center_point.name)[1]
                plus_point_node = find_cell_name(self.smg.not_inf_nodes, PointCell, plus_point.name)[1]
                minus_point_node = find_cell_name(self.smg.not_inf_nodes, PointCell, minus_point.name)[1]
                plus_routes, ni_plus = self.smg.routes_node_to_node(center_point_node, plus_point_node)
                minus_routes, ni_minus = self.smg.routes_node_to_node(center_point_node, minus_point_node)
                if not plus_routes:
                    raise MBEquipmentError("Route from central point to '+' point not found",
                                           AttributeErrorData(cls_name, obj_name, "dir_plus_point"))
                if not minus_routes:
                    raise MBEquipmentError("Route from central point to '-' point not found",
                                           AttributeErrorData(cls_name, obj_name, "dir_minus_point"))
                for plus_route in plus_routes:
                    for minus_route in minus_routes:
                        if plus_route.partially_overlaps(minus_route):
                            raise MBEquipmentError("Cannot understand '+' and '-' directions because their overlaps",
                                                   AttributeErrorData(cls_name, obj_name, "dir_minus_point"))
                if not (ni_plus is ni_minus):
                    raise MBEquipmentError("Defined '+' or '-' direction is equal to 0-direction",
                                           AttributeErrorData(cls_name, obj_name, "dir_minus_point"))

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

        for image in self.images:
            image_name = image.name
            cls_name = image.__class__.__name__
            obj_name = image_name

            if isinstance(image, BorderSOI):
                point_node: PolarNode = find_cell_name(self.smg.not_inf_nodes, PointCell, image.attr_confirmed_value("point").name)[1]
                inf_ni_str = None
                if point_node in self.smg.nodes_inf_connected:
                    inf_ni_str = self.smg.nodes_inf_connected[point_node].opposite_end_str

                model_object = BorderMO(image.attr_confirmed_value("border_type"), inf_ni_str)
                point_node.append_cell_obj(BorderCell(image_name))
                model_object.name = image_name
                self.names_mo["Border"][image_name] = model_object

    def build_sections(self):

        for image in self.images:
            image_name = image.name
            cls_name = image.__class__.__name__
            obj_name = image_name

            if isinstance(image, SectionSOI):
                border_points: list[PointMO] = [self.names_mo["Point"][point.name] for point in image.attr_confirmed_value("border_points")]
                point_nodes: list[PolarNode] = [find_cell_name(self.smg.not_inf_nodes, PointCell, point.name)[1]
                                                for point in border_points]
                closed_links, closed_nodes = self.smg.closed_links_nodes(point_nodes)
                if not closed_links:
                    raise MBEquipmentError("No closed links found",
                                           AttributeErrorData(cls_name, obj_name, "border_points"))

                # check links sections and make cells
                for link in closed_links:
                    try:
                        element_cell_by_type(link, IsolatedSectionCell)
                    except NotFoundCellError:
                        pass
                    else:
                        raise MBEquipmentError("Section in link already exists",
                                               AttributeErrorData(cls_name, obj_name, "border_points"))
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
                    # if not light_names:
                    #     raise MBEquipmentError(cls_name, obj_name,
                    #                            "Found segment section |-----| with 0 border lights")
                    if len(light_names) == 2:
                        section_type = CESectionType(CESectionType.shunt_stop)
                        for light_name in light_names:
                            light: LightMO = self.names_mo['Light'][light_name]
                            link_ni = light_names[light_name]
                            if (light.route_type == "train") and (link_ni.end != light.end_forward_tpl1):
                                section_type = CESectionType(CESectionType.track)
                                break
                    else:
                        section_type = CESectionType(CESectionType.indic)

                model_object = SectionMO(section_type, rail_points)
                model_object.name = image_name
                self.names_mo["Section"][image_name] = model_object

    def eval_routes(self, dir_name):

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
            if light.route_type == "train":
                try:
                    element_cell_by_type(start_ni.pn, BorderCell)
                except NotFoundCellError:
                    pass
                else:
                    is_enter_signal = True

            # 1.1 Slices extraction
            for route in routes:

                # 1.1.1 Train routes slices extraction
                if light.route_type == "train":

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
                                if light_found.route_type == "train":
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
                            if (light.route_type == "train") and\
                               (border_found.border_type == "standoff"):
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
                if end_section.section_type == "track":
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
                    if (end_section.section_type == "indic") or \
                            (end_section.section_type == "shunt_stop"):
                        trace_end = end_section.name
                    else:
                        trace_end = border_cell.name

                shunting_route.trace_end = trace_end

                # finish_selectors
                finish_selectors = [end_light_name]
                if (end_section.section_type == "track") or\
                        (end_section.section_type == "shunt_stop"):
                    node_before_end = shunting_route_slice.nodes[-2]
                    before_end_light_cell: LightCell = element_cell_by_type(node_before_end, LightCell)
                    if before_end_light_cell.name not in finish_selectors:
                        finish_selectors.append(before_end_light_cell.name)
                shunting_route.end_selectors = " ".join(finish_selectors)

                route_id += 1
                shunting_routes.append(shunting_route)

            if light.route_type == "train":
                train_light_routes_dict[light.name] = (train_routes, shunting_routes)
            else:
                shunting_light_routes_dict[light.name] = shunting_routes

        # 2. Xml formation
        form_rail_routes_xml(train_light_routes_dict, shunting_light_routes_dict, dir_name,
                             "TrainRoute.xml", "ShuntingRoute.xml")
