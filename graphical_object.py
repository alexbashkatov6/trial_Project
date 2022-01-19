from __future__ import annotations
import math
import numpy as np
from abc import ABC, abstractmethod
from typing import Union
from numbers import Real

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from nv_config import ANGLE_EQUAL_EVAL_PRECISION, ANGLE_EQUAL_VIEW_PRECISION, COORD_EQUAL_PRECISION, H_CLICK_ZONE
from custom_enum import CustomEnum


class CECurveType(CustomEnum):
    line_segment = 0
    bezier = 1
    optimal_bezier = 2


class CEMaxMin(CustomEnum):
    max = 0
    min = 1


class GeometryException(Exception):
    pass


class EquivalentLinesException(GeometryException):
    pass


class ParallelLinesException(GeometryException):
    pass


class PointsEqualException(GeometryException):
    pass


class OutBorderException(GeometryException):
    pass


def cut_optimization(func, *args, borders: tuple[Real, Real], maxormin: CEMaxMin = CEMaxMin('min'),
                     precision: float = ANGLE_EQUAL_EVAL_PRECISION) -> tuple[float, float]:
    # print("given params: borders: {}, maxormin {}, precision {}".format(borders, maxormin, precision))
    """ CUT 1D optimization for convex functions """
    curr_borders = (min(borders), max(borders))
    curr_region_size = curr_borders[1] - curr_borders[0]
    if maxormin == 'min':
        k = 1
    else:
        k = -1
    while curr_region_size > precision:
        # if maxormin == 'min':
        #     print("curr_borders", curr_borders)
        center_point = 0.5 * (curr_borders[0] + curr_borders[1])
        epsilon_vals = k * func(center_point-precision, *args), k * func(center_point+precision, *args)
        if epsilon_vals[1] > epsilon_vals[0]:
            curr_borders = curr_borders[0], 0.5 * (curr_borders[0] + curr_borders[1])
        else:
            curr_borders = 0.5 * (curr_borders[0] + curr_borders[1]), curr_borders[1]
        curr_region_size /= 2

        curr_f_value = k * min(epsilon_vals)
        curr_x_value = curr_borders[0]

    return curr_x_value, curr_f_value


def distance(pnt_1: Point2D, pnt_2: Point2D) -> float:
    return math.dist(pnt_1.coords, pnt_2.coords)


def coord_equality(coord_1: float, coord_2: float, coord_precision: float = None) -> bool:
    if not coord_precision:
        coord_precision = COORD_EQUAL_PRECISION
    return abs(coord_1 - coord_2) < coord_precision


def evaluate_vector(pnt_1: Point2D, pnt_2: Point2D) -> (Angle, bool):
    """ returns angle and if direction from pnt_1 to pnt_2 is positive """
    coord_eq_prec = COORD_EQUAL_PRECISION
    max_cycle_count = 5
    while True:
        if not max_cycle_count:
            raise PointsEqualException('Given points are equal')
        max_cycle_count -= 1
        if coord_equality(pnt_1.y, pnt_2.y, coord_eq_prec) and coord_equality(pnt_1.x, pnt_2.x, coord_eq_prec):
            coord_eq_prec *= COORD_EQUAL_PRECISION
        else:
            break
    if coord_equality(pnt_1.y, pnt_2.y, coord_eq_prec):
        if ANGLE_EQUAL_EVAL_PRECISION * abs(pnt_1.x - pnt_2.x) > abs(pnt_1.y - pnt_2.y):
            return Angle(0), pnt_2.x > pnt_1.x
    if coord_equality(pnt_1.x, pnt_2.x, coord_eq_prec):
        if ANGLE_EQUAL_EVAL_PRECISION * abs(pnt_1.y - pnt_2.y) > abs(pnt_1.x - pnt_2.x):
            return Angle(math.pi / 2), pnt_2.y > pnt_1.y
    return Angle(math.atan((pnt_1.y - pnt_2.y) / (pnt_1.x - pnt_2.x))), pnt_2.x > pnt_1.x


def rotate_operation(center: Point2D, point: Point2D, angle: Angle) -> Point2D:
    current_angle, direction_is_positive = evaluate_vector(center, point)
    if not direction_is_positive:
        current_angle += math.pi
    new_angle = current_angle + angle.angle_0_2pi
    r = math.dist(point.coords, center.coords)
    return Point2D(center.x + r * math.cos(new_angle.angle_0_2pi), center.y + r * math.sin(new_angle.angle_0_2pi))


def lines_intersection(line_1: Line2D, line_2: Line2D) -> Point2D:
    if line_1.angle == line_2.angle:
        if coord_equality(line_1.c, line_2.c):
            raise EquivalentLinesException('Lines {}, {} are equal'.format(line_1, line_2))
        raise ParallelLinesException('Angles of lines {}, {} are equal'.format(line_1, line_2))
    result = np.linalg.solve(np.array([[line_1.a, line_1.b], [line_2.a, line_2.b]]), np.array([-line_1.c, -line_2.c]))
    return Point2D(result[0], result[1])


def normal(pnt: Point2D, line: Line2D) -> tuple[Line2D, Point2D]:
    angle_normal = line.angle + math.pi/2
    line_normal = Line2D(pnt, angle=angle_normal)
    return line_normal, lines_intersection(line, line_normal)


def pnt_between(pnt: Point2D, pnt_1: Point2D, pnt_2: Point2D) -> bool:
    assert Line2D(pnt, pnt_1).angle == Line2D(pnt, pnt_2).angle, "Points not on 1 line"
    return (distance(pnt, pnt_1) <= distance(pnt_1, pnt_2)) and (distance(pnt, pnt_2) <= distance(pnt_1, pnt_2))


def bezier_curvature(t: Real, pnt_1: Point2D, pnt_2: Point2D, pnt_control: Point2D):
    """ t is float between 0 and 1 """
    x1, y1 = pnt_1.coords
    x2, y2 = pnt_2.coords
    x3, y3 = pnt_control.coords
    return abs(0.5 * (-(2 * (x3 - x1) + x1 - x2) * (2 * (y3 - y1) * t - (y3 - y1) + t * y1 - t * y2) +
                      (2 * (y3 - y1) + y1 - y2) * (2 * (x3 - x1) * t - (x3 - x1) + t * x1 - t * x2)) *
               ((2 * (x3 - x1) * t - (x3 - x1) + t * x1 - t * x2) ** 2 + (
                       2 * (y3 - y1) * t - (y3 - y1) + t * y1 - t * y2) ** 2) ** (-1.5))


class Point2D:
    def __init__(self, *args):
        """ Point2D(Real, Real) Point2D(tuple[Real, Real]) """
        if type(args[0]) == tuple:
            assert len(args) == 1, 'Unexpected second arg for first is tuple'
            assert len(args[0]) == 2, 'Should be 2 args in tuple'
            assert all(isinstance(i, Real) for i in args[0]), 'Values should be real'
            self.x = float(args[0][0])
            self.y = float(args[0][1])
        else:
            assert len(args) == 2, 'Expected 2 args'
            assert all(isinstance(i, Real) for i in args), 'Values should be real'
            self.x = float(args[0])
            self.y = float(args[1])

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.x, self.y)

    __str__ = __repr__

    @property
    def coords(self):
        return self.x, self.y

    # @property
    # def x(self):
    #     return self.x


class Angle:
    """ angle is measured clockwise """
    def __init__(self, free_angle: Real):
        self.free_angle = float(free_angle)

    def __add__(self, other):
        assert isinstance(other, (Real, Angle)), 'Can add only angle or int/float'
        if isinstance(other, Real):
            return Angle(self.free_angle + other)
        else:
            return Angle(self.free_angle + other.free_angle)

    def __eq__(self, other):
        assert isinstance(other, (Real, Angle)), 'Can compare only angle or int/float'
        if isinstance(other, Real):
            return abs(self.angle_mpi2_ppi2 - other) < ANGLE_EQUAL_EVAL_PRECISION
        else:
            return abs(self.angle_mpi2_ppi2 - other.angle_mpi2_ppi2) < ANGLE_EQUAL_EVAL_PRECISION

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "{}({:1.7f})".format(self.__class__.__name__, self.angle_mpi2_ppi2)

    __str__ = __repr__

    @property
    def angle_0_2pi(self):
        """ radian value in interval [0, 2pi) """
        positive_angle = self.free_angle % (2 * math.pi)
        return positive_angle

    @property
    def deg_angle_0_360(self):
        """ degree value in interval [0, 360) """
        return self.angle_0_2pi * 180 / math.pi

    @property
    def angle_mpi2_ppi2(self):
        """ radian value in interval (-pi/2, pi/2] """
        positive_angle = self.free_angle % math.pi
        return positive_angle - math.pi if positive_angle > math.pi / 2 else positive_angle

    @property
    def deg_angle_m90_p90(self):
        """ degree value in interval (-90, 90] """
        return self.angle_mpi2_ppi2 * 180 / math.pi


class Line2D:
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D = None, angle: Angle = None):
        """ Line is solution of equation a*x + b*y + c = 0 """
        assert not (pnt_2 is None) or not (angle is None), 'Not complete input data'
        self.pnt = pnt_1
        if angle:
            self.angle = angle
        else:
            self.angle = evaluate_vector(pnt_1, pnt_2)[0]
        self.a = -math.sin(self.angle.angle_mpi2_ppi2)
        self.b = math.cos(self.angle.angle_mpi2_ppi2)
        self.c = -self.a * self.pnt.x - self.b * self.pnt.y
        self.round_abc()

    def __repr__(self):
        return "{}({}, angle={})".format(self.__class__.__name__, self.pnt, self.angle)

    __str__ = __repr__

    def round_abc(self):
        if self.angle == 0:
            self.a = 0
            self.b = 1
            self.c = -self.pnt.y
            return
        if self.angle == (math.pi / 2):
            self.a = 1
            self.b = 0
            self.c = -self.pnt.x
            return


class GeometryPrimitive(ABC):

    @abstractmethod
    def draw_parameters(self):
        pass


class BoundedCurve(GeometryPrimitive):
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D, angle_1: Angle = None, angle_2: Angle = None):
        self.pnt_1 = pnt_1
        self.pnt_2 = pnt_2
        evaluate_vector(pnt_1, pnt_2)  # for equal points check
        if angle_1 is None and angle_2 is None:
            self.geom_type = CECurveType('line_segment')
        elif angle_2 is None:
            self.geom_type = CECurveType('optimal_bezier')
            self.angle_1 = angle_1
        else:
            self.geom_type = CECurveType('bezier')
            self.angle_1 = angle_1
            self.angle_2 = angle_2
        if self.geom_type != 'line_segment':
            self.check_not_on_line()
        if self.geom_type == 'optimal_bezier':
            self.angle_2 = self.bezier_optimization()

    def __repr__(self):
        if self.geom_type == 'line_segment':
            return "{}({}, {})".format(self.__class__.__name__, self.pnt_1, self.pnt_2)
        else:
            return "{}({}, {}, {}, {})".format(self.__class__.__name__,
                                               self.pnt_1, self.pnt_2, self.angle_1, self.angle_2)

    def check_not_on_line(self):
        angle_between = Line2D(self.pnt_1, self.pnt_2).angle
        if self.angle_1 == angle_between:
            self.geom_type = CECurveType('line_segment')
        if (self.geom_type == 'bezier') and (self.angle_2 == angle_between):
            self.geom_type = CECurveType('line_segment')

    @property
    def bezier_control_point(self) -> Point2D:
        return lines_intersection(Line2D(self.pnt_1, angle=self.angle_1), Line2D(self.pnt_2, angle=self.angle_2))

    def bezier_optimization(self) -> Angle:
        float_angle_1 = self.angle_1.angle_mpi2_ppi2
        # print("in optim", float_angle_1, (float_angle_1 + ANGLE_EQUAL_VIEW_PRECISION,
        #                                   float_angle_1 + math.pi - ANGLE_EQUAL_VIEW_PRECISION))
        # print("optim result", cut_optimization(self.max_curvature,
        #                               borders=(float_angle_1 + ANGLE_EQUAL_VIEW_PRECISION,
        #                                        float_angle_1 + math.pi - ANGLE_EQUAL_VIEW_PRECISION))[0])
        return Angle(cut_optimization(self.max_curvature,
                                      borders=(float_angle_1 + ANGLE_EQUAL_VIEW_PRECISION,
                                               float_angle_1 + math.pi - ANGLE_EQUAL_VIEW_PRECISION))[0])

    def max_curvature(self, float_angle: float) -> float:
        angle = Angle(float_angle)
        pnt_intersect = lines_intersection(Line2D(self.pnt_1, angle=self.angle_1), Line2D(self.pnt_2, angle=angle))
        return cut_optimization(bezier_curvature, self.pnt_1, self.pnt_2, pnt_intersect,
                                borders=(0, 1), maxormin=CEMaxMin('max'))[1]

    def point_by_param(self, t: Real) -> Point2D:
        x1, y1 = self.pnt_1.coords
        x2, y2 = self.pnt_2.coords
        if self.geom_type == 'line_segment':
            x = x1 + t*(x2-x1)
            y = y1 + t*(y2-y1)
        else:
            x3, y3 = self.bezier_control_point.coords
            x = t*(t*x2 + (1 - t)*((x3-x1) + x1)) + (1 - t)*(t*((x3-x1) + x1) + x1*(1 - t))
            y = t*(t*y2 + (1 - t)*((y3-y1) + y1)) + (1 - t)*(t*((y3-y1) + y1) + y1*(1 - t))
        return Point2D(x, y)

    def y_by_x(self, x: Real) -> float:
        x1, y1 = self.pnt_1.coords
        x2, y2 = self.pnt_2.coords
        if (x < min(x1, x2)) or (x > max(x1, x2)):
            raise OutBorderException("Given x is not in borders")
        t = cut_optimization(lambda s: abs(self.point_by_param(s).x-x),
                             borders=(0, 1), maxormin=CEMaxMin('min'), precision=COORD_EQUAL_PRECISION)[0]
        return self.point_by_param(t).y

    def angle_by_param(self, t: Real) -> Angle:
        if self.geom_type == 'line_segment':
            return Line2D(self.pnt_1, self.pnt_2).angle
        x1, y1 = self.pnt_1.coords
        x2, y2 = self.pnt_2.coords
        x3, y3 = self.bezier_control_point.coords
        dx_dt = -4*(x3-x1)*t + 2*(x3-x1) - 2*t*x1 + 2*t*x2
        dy_dt = -4*(y3-y1)*t + 2*(y3-y1) - 2*t*y1 + 2*t*y2
        pnt = self.point_by_param(t)
        pnt_direction = Point2D(pnt.x + dx_dt, pnt.y + dy_dt)
        return Line2D(pnt, pnt_direction).angle

    def t_devision(self):
        if self.geom_type == 'line_segment':
            return [0, 1]
        devision = [0]
        count = 10
        nominal_step = 1/count
        current_step = nominal_step
        while True:
            t = devision[-1]
            next_t = t + current_step
            angle_t = self.angle_by_param(t)
            angle_t_delta_t = self.angle_by_param(next_t)
            if abs(Angle(angle_t.free_angle - angle_t_delta_t.free_angle).angle_0_2pi) > 1e2*ANGLE_EQUAL_VIEW_PRECISION:
                current_step = current_step/2
                continue
            else:
                if current_step < nominal_step:
                    current_step *= 2
                else:
                    current_step = nominal_step
                devision.append(next_t)
            if 1-next_t < nominal_step/10:
                break
        if devision[-1] > 1:
            devision[-1] = 1
        return devision

    def draw_parameters(self):
        if self.geom_type == 'line_segment':
            return 'line_segment', *self.pnt_1.coords, *self.pnt_2.coords
        else:
            return 'bezier', *self.pnt_1.coords, *self.bezier_control_point.coords, *self.pnt_2.coords


class Ellipse(GeometryPrimitive):
    def __init__(self):
        pass

    def draw_parameters(self):
        pass


class FrameCS:
    def __init__(self, base_cs: FrameCS = None, center_pnt_in_base: Point2D = Point2D(0, 0),
                 scale_in_base_x: Real = 1, scale_in_base_y: Real = 1):
        """ scale > 1 means that ticks more often """
        self._base_cs = base_cs
        self._center_pnt_in_base = center_pnt_in_base
        self._scale_in_base_x = scale_in_base_x
        self._scale_in_base_y = scale_in_base_y

        self._is_base = base_cs is None
        self._scale_absolute_x = 1
        self._scale_absolute_y = 1
        self._center_pnt_absolute_x = 0
        self._center_pnt_absolute_y = 0
        self.eval_absolute_parameters()

    @property
    def is_base(self):
        return self._is_base

    @property
    def base_cs(self):
        return self._base_cs

    @property
    def center_pnt_in_base(self) -> Point2D:
        return self._center_pnt_in_base

    @center_pnt_in_base.setter
    def center_pnt_in_base(self, value):
        self._center_pnt_in_base = value
        self.eval_absolute_parameters()

    @property
    def scale_in_base_x(self):
        return self._scale_in_base_x

    @scale_in_base_x.setter
    def scale_in_base_x(self, value):
        self._scale_in_base_x = value
        self.eval_absolute_parameters()

    @property
    def scale_in_base_y(self):
        return self._scale_in_base_y

    @scale_in_base_y.setter
    def scale_in_base_y(self, value):
        self._scale_in_base_y = value
        self.eval_absolute_parameters()

    @property
    def center_pnt_absolute_x(self):
        return self._center_pnt_absolute_x

    @property
    def center_pnt_absolute_y(self):
        return self._center_pnt_absolute_y

    @property
    def scale_absolute_x(self):
        return self._scale_absolute_x

    @property
    def scale_absolute_y(self):
        return self._scale_absolute_y

    def eval_absolute_parameters(self):
        if not self.is_base:
            self._scale_absolute_x = self.base_cs.scale_absolute_x * self._scale_in_base_x
            self._scale_absolute_y = self.base_cs.scale_absolute_y * self._scale_in_base_y
            self._center_pnt_absolute_x = self.base_cs.center_pnt_absolute_x + self._center_pnt_in_base.x
            self._center_pnt_absolute_y = self.base_cs.center_pnt_absolute_y + self._center_pnt_in_base.y


class FramePoint:
    def __init__(self, pnt: Point2D, cs: FrameCS):
        self._pnt = pnt
        self._cs = cs

    @property
    def pnt(self):
        return self._pnt

    @property
    def cs(self):
        return self._cs

    def reevaluate_in_cs(self, cs: FrameCS) -> Point2D:
        pnt_abs_x = self.pnt.x / self.cs.scale_absolute_x + self.cs.center_pnt_absolute_x
        pnt_abs_y = self.pnt.y / self.cs.scale_absolute_y + self.cs.center_pnt_absolute_y
        pnt_new_x = (pnt_abs_x - cs.center_pnt_absolute_x) * cs.scale_absolute_x
        pnt_new_y = (pnt_abs_y - cs.center_pnt_absolute_y) * cs.scale_absolute_y
        return Point2D(pnt_new_x, pnt_new_y)


class FrameAngle:
    def __init__(self, angle: Angle, cs: FrameCS):
        self._angle = angle
        self._cs = cs

    @property
    def angle(self):
        return self._angle

    @property
    def cs(self):
        return self._cs

    def reevaluate_in_cs(self, cs: FrameCS) -> Angle:
        if self.angle == math.pi / 2:
            return self.angle
        else:
            return Angle(math.atan(math.tan(self.angle.angle_0_2pi) *
                                   cs.scale_absolute_x * self.cs.scale_absolute_y
                                   / cs.scale_absolute_y / self.cs.scale_absolute_x))


def distance_in_frame(f: Frame, fp_1: FramePoint, fp_2: FramePoint):
    return distance(fp_1.reevaluate_in_cs(f.center_fcs), fp_2.reevaluate_in_cs(f.center_fcs))


class FPViewProperties:
    def __init__(self):
        self.visible = True
        self.line_weight = 1
        self.line_dashed = False
        self.line_color = 'black'


class FramePrimitive(ABC):

    @abstractmethod
    # @property
    def view_properties(self) -> FPViewProperties:
        pass

    @abstractmethod
    # @property
    def connected_frame(self) -> Frame:
        pass

    @abstractmethod
    def reevaluate(self) -> GeometryPrimitive:
        pass

    @abstractmethod
    def point_in_clickable_area(self, pnt: Point2D) -> bool:
        pass


class FPBoundedCurve(FramePrimitive):

    @property
    def view_properties(self) -> FPViewProperties:
        pass

    @property
    def connected_frame(self) -> Frame:
        pass

    def reevaluate(self) -> GeometryPrimitive:
        pass

    def point_in_clickable_area(self, pnt: Point2D) -> bool:
        pass


class Frame(QObject):
    def __init__(self, base_frame: BaseFrame = None):
        super().__init__()
        if base_frame:
            self.center_fcs: FrameCS = FrameCS(base_frame.center_fcs)
        else:
            self.center_fcs: FrameCS = FrameCS()
        self.corner_fcs: FrameCS = FrameCS(self.center_fcs)
        self.fpoints: list[FramePoint] = []
        self.fprimitives: list[FramePrimitive] = []
        self.width: Real = 1
        self.height: Real = 1
        self._width_to_height_ratio: Real = 1

    @property
    def width_to_height_ratio(self):
        return self._width_to_height_ratio

    @width_to_height_ratio.setter
    def width_to_height_ratio(self, value):
        self._width_to_height_ratio = value


class BaseFrame(Frame):
    def __init__(self):
        super().__init__()
        self.additional_fcs_list: list[FrameCS] = []
        # show_border is border for capture frame
        self.show_border_h: Real = 0.05  # percent from h
        self.show_border_w: Real = 0.05  # percent from w
        # gl_padding is border for region where for each GL 1 point at least
        self.gl_padding_h: Real = 0.05  # percent from h
        self.gl_padding_w: Real = 0.05  # percent from w

    @pyqtSlot(tuple)
    def pa_coordinates_changed(self, new_coords: tuple[tuple[int, int], tuple[int, int]]):
        print('got pa coords', new_coords[0][0], new_coords[0][1], new_coords[1][0], new_coords[1][1])
        # H_CLICK_ZONE

    @pyqtSlot(tuple)
    def zoom_in_selection_coordinates(self, select_coords: tuple[tuple[int, int], tuple[int, int]]):
        print('got zoom in select coords', select_coords[0][0], select_coords[0][1], select_coords[1][0],
              select_coords[1][1])
        # H_CLICK_ZONE

    @pyqtSlot(tuple)
    def zoom_out_selection_coordinates(self, select_coords: tuple[tuple[int, int], tuple[int, int]]):
        print('got zoom out select coords', select_coords[0][0], select_coords[0][1], select_coords[1][0],
              select_coords[1][1])
        # H_CLICK_ZONE

    @pyqtSlot(dict)
    def got_obj_created(self, obj_info: dict):
        print('got obj_created in BaseFrame', obj_info)


# class ContinuousVisibleArea(QObject):
#
#     def __init__(self):
#         super().__init__()
#         self.current_scale = 1.  # px/m
#         self.upleft_x = None
#
#     @pyqtSlot(tuple)
#     def pa_coordinates_changed(self, new_coords: tuple[tuple[int, int], tuple[int, int]]):
#         print('got pa coords', new_coords[0][0], new_coords[0][1], new_coords[1][0], new_coords[1][1])
#         # H_CLICK_ZONE
#
#     @pyqtSlot(tuple)
#     def zoom_in_selection_coordinates(self, select_coords: tuple[tuple[int, int], tuple[int, int]]):
#         print('got zoom in select coords', select_coords[0][0], select_coords[0][1], select_coords[1][0],
#               select_coords[1][1])
#         # H_CLICK_ZONE
#
#     @pyqtSlot(tuple)
#     def zoom_out_selection_coordinates(self, select_coords: tuple[tuple[int, int], tuple[int, int]]):
#         print('got zoom out select coords', select_coords[0][0], select_coords[0][1], select_coords[1][0],
#               select_coords[1][1])
        # H_CLICK_ZONE


if __name__ == '__main__':
    test_1 = False
    if test_1:
        p1 = Point2D(10, 20)
        print('p1 x y = ', p1.x, p1.y)
        p2 = Point2D((12, 13))
        print('p2 x y = ', p2.x, p2.y)
        # r1 = Rect(10, 20, 300, 400)
        # print('r1 center angle = ', r1.center, r1.angle, r1.w, r1.h)
        # r2 = Rect(w=10, h=20, center=Point2D(300, 400))
        # print('r2 center angle = ', r2.center, r2.angle, r2.w, r2.h)
        # r3 = Rect((300, 400), 0, 10, 20)
        # print('r3 center angle = ', r3.center, r3.angle, r3.w, r3.h)
        a = Angle(math.pi)
        print(a.angle_mpi2_ppi2)
        print(evaluate_vector(Point2D(1e-7, 0), Point2D(0, 0))[0].deg_angle_m90_p90)
        line_ = Line2D(Point2D(0, 1), Point2D(3, 2))
        print(line_.a, line_.b, line_.c)
        b = Angle(-2 * math.pi + 0.001)
        print(b.angle_0_2pi)
        print(math.dist((0, 0), (1, 1)))
        print(rotate_operation(Point2D(0, 0), Point2D(0, 1), Angle(math.pi / 2)).coords)
        print(lines_intersection(Line2D(Point2D(0, 0), Point2D(1, 1)), Line2D(Point2D(1, 1), Point2D(2, 0))).coords)

        # bc = BezierCurve(Point2D(100, 100), Angle(0), Point2D(300, 200), Angle(math.pi * 0.25))
        # print(bc.display_params())


    # class Rect:
    #     def __init__(self, x: Union[Real, Point2D] = None, y: Union[Real, Angle] = None, w: Real = None, h: Real = None,
    #                  center: Point2D = None, angle: Angle = None):
    #         """ docstring """
    #         if type(x) == Point2D:
    #             center = x
    #             angle = y
    #             x = None
    #             y = None
    #         assert not (w is None) & (not (h is None)), 'Width and height should be defined'
    #         assert ((not (x is None)) & (not (y is None)) & (angle is None)) | \
    #                ((not (center is None)) & (not (angle is None))), 'Not complete input data'
    #
    #         if angle is None:
    #             angle = Angle(0)
    #         if not (x is None):
    #             self.center = Point2D(float(x + w / 2), float(y + h / 2))
    #             self.angle = Angle(0)
    #         else:
    #             self.center = center
    #             self.angle = angle
    #         self.center: Point2D
    #         self.angle: Angle
    #         self.w = w
    #         self.h = h
    #
    #     def includes_point(self, p: Point2D):
    #         """border includes points too"""
    #         rot_point = rotate_operation(self.center, p, Angle(-self.angle.free_angle))
    #         print('rot_point', rot_point)
    #         return (self.center.x - self.w / 2 <= rot_point.x <= self.center.x + self.w / 2) & \
    #                (self.center.y - self.h / 2 <= rot_point.y <= self.center.y + self.h / 2)


        # r = Rect(Point2D(7, 5), Angle(-26.565 * math.pi / 180), 8.944, 4.472)
        # print(r.includes_point(Point2D(3, 8)))

        # Point2D((6,))

        # center_fcs = FrameCS()
        # center_fcs = FrameCS(center_fcs, Point2D(10, 20), 2, 2)
        # sec_cs = FrameCS(center_fcs, Point2D(10, 20), 3, 2)
        # print(sec_cs.center_pnt_absolute_x, sec_cs.center_pnt_absolute_y, sec_cs.scale_absolute_x, sec_cs.scale_absolute_y)

        # def transform_coordinates(pnt: Point2D, cs_base: FrameCS, cs_new: FrameCS) -> Point2D:
        #     pnt_abs_x = pnt.x / cs_base.scale_absolute_x + cs_base.center_pnt_absolute_x
        #     pnt_abs_y = pnt.y / cs_base.scale_absolute_y + cs_base.center_pnt_absolute_y
        #     pnt_new_x = (pnt_abs_x - cs_new.center_pnt_absolute_x) * cs_new.scale_absolute_x
        #     pnt_new_y = (pnt_abs_y - cs_new.center_pnt_absolute_y) * cs_new.scale_absolute_y
        #     return Point2D(pnt_new_x, pnt_new_y)
        #     print(transform_coordinates(Point2D(3, 2), center_fcs, sec_cs))

        base_cs_ = FrameCS()
        center_cs = FrameCS(base_cs_, Point2D(3.5, 2), 2, 2)
        sec_cs = FrameCS(base_cs_, Point2D(3, 1), 0.5, 0.5)

        sec_cs.center_pnt_in_base = Point2D(3, 2)
        fp = FramePoint(Point2D(3, 2), center_cs)
        curved_cs = FrameCS(base_cs_, Point2D(3, 1), 1, 0.5)
        fa = FrameAngle(Angle(math.pi / 4), base_cs_)

        print(fp.reevaluate_in_cs(sec_cs))
        print(fa.reevaluate_in_cs(center_cs).deg_angle_0_360)
        print(fa.reevaluate_in_cs(curved_cs).deg_angle_0_360)


        # print(math.tan(math.pi/2))

        def parabola(x):
            return (x - 3) ** 2 + 2


        def bez(x):
            return (x - 3) ** 2 + 2


        print(cut_optimization(parabola, borders=(1, 5)))
        # print(bezier_curvature(0, Point2D(100, 100), Point2D(300, 100), Point2D(300, 200)))
        print(cut_optimization(bezier_curvature, Point2D(100, 100), Point2D(300, 200), Point2D(300, 100), borders=(0, 1)))


        # def max_curvature(float_angle: float):
        #     angle = Angle(float_angle)
        #     pnt_1 = Point2D(1, 1)
        #     angle_1 = Angle(math.pi / 4)
        #     pnt_2 = Point2D(3, 1)
        #     pnt_intersect = lines_intersection(Line2D(pnt_1, angle=angle_1), Line2D(pnt_2, angle=angle))
        #     print(pnt_intersect)
        #     return cut_optimization(bezier_curvature, pnt_1, pnt_2, pnt_intersect,
        #                             borders=(0, 1), maxormin=BSSMaxMin('max'))[1]
        #
        #
        # # print(max_curvature(-math.pi/4))
        # print(cut_optimization(max_curvature, borders=(math.pi / 4 + 0.01, math.pi + math.pi / 4 - 0.01)))
        # print(Angle(2.3561937459466598).deg_angle_0_360)
        # print(bezier_curvature(0.0, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
        # print(bezier_curvature(0.2, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
        # print(bezier_curvature(0.4, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
        # print(bezier_curvature(0.6, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
        # print(bezier_curvature(0.8, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
        # print(bezier_curvature(1.0, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))

        bc = BoundedCurve(Point2D(1, 1), Point2D(3, 1))
        bc_2 = BoundedCurve(Point2D(1, 1), Point2D(3, 1), Angle(math.pi/4), Angle(math.pi/2))
        bc_3 = BoundedCurve(Point2D(1, 1), Point2D(3, 1), Angle(math.pi/4))
        print("here")
        bc_4 = BoundedCurve(Point2D(1, 1), Point2D(3, 1), Angle(0))
        # bc_5 = BoundedCurve(Point2D(1, 1), Point2D(3, 1), Angle(math.pi/4), Angle(math.pi/4))

        print()
        print("draw_parameters")
        print(bc.draw_parameters())
        print(bc_2.draw_parameters())
        print(bc_3.draw_parameters())
        print(bc_4.draw_parameters())
        # print(bc_5.draw_parameters())

        print()
        print(distance(Point2D(1, 1), Point2D(2, 2)))
        print(normal(Point2D(1, 1), Line2D(Point2D(2, 2), Point2D(3, 1))))
        print(pnt_between(Point2D(2, 2), Point2D(1, 1), Point2D(3, 3)))

        print()
        print("point_by_param")
        print(bc.point_by_param(0), bc.point_by_param(0.5), bc.point_by_param(1))
        print(bc_2.point_by_param(0), bc_2.point_by_param(0.5), bc_2.point_by_param(1))
        print(bc_3.point_by_param(0), bc_3.point_by_param(0.5), bc_3.point_by_param(1))

        print()
        print("angle_by_param")
        print(bc.angle_by_param(0), bc.angle_by_param(0.5), bc.angle_by_param(1))
        print(bc_2.angle_by_param(0), bc_2.angle_by_param(0.15424156188964), bc_2.angle_by_param(0.5), bc_2.angle_by_param(1))
        print(bc_3.angle_by_param(0), bc_3.angle_by_param(0.5), bc_3.angle_by_param(1))

        print()
        print("sep")
        sep = bc_3.t_devision()
        print(sep)
        print(len(sep))

        # lines_intersection(Line2D(Point2D(0,0), angle=Angle(0)), Line2D(Point2D(0,1), angle=Angle(0)))

        print()
        print("y by x")
        print(bc_3.y_by_x(2))

        # bc_5 = BoundedCurve(Point2D(1, 1), Point2D(1, 1))  # , Angle(0)

        bc_station = BoundedCurve(Point2D(650.0, 0.0), Point2D(525.0, -2.5), Angle(0))
        print(bc_station)
        for i in range(20):
            print((i*2*math.pi/20+0.001)*180/math.pi, bc_station.max_curvature(i*2*math.pi/20+0.001))

    test_2 = True
    if test_2:
        bc_station = BoundedCurve(Point2D(650.0, 0.0), Point2D(525.0, -2.5), Angle(math.pi))
        print(bc_station)


