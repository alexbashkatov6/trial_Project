from __future__ import annotations
import math
import numpy as np
from abc import ABC, abstractmethod
from typing import Union
from numbers import Real

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from nv_config import ANGLE_EQUAL_PRECISION, COORD_EQUAL_PRECISION, H_CLICK_ZONE
from nv_bounded_string_set_class import bounded_string_set

BSSCurveType = bounded_string_set('BSSCurveType', [['line_segment'], ['bezier'], ['optimal_bezier']])
BSSMaxMin = bounded_string_set('BSSMaxMin', [['max'], ['min']])


def cut_optimization(func, *args, borders: tuple[Real, Real], maxormin: BSSMaxMin = BSSMaxMin('min'),
                     precision: float = ANGLE_EQUAL_PRECISION) -> tuple[float, float]:
    """CUT 1D optimization for convex functions"""
    curr_borders = (min(borders), max(borders))
    curr_region_size = curr_borders[1] - curr_borders[0]
    if maxormin == 'min':
        k = 1
    else:
        k = -1
    while curr_region_size > precision:
        border_vals = k * func(curr_borders[0], *args), k * func(curr_borders[1], *args)
        if border_vals[1] > border_vals[0]:
            curr_borders = curr_borders[0], 0.5 * (curr_borders[0] + curr_borders[1])
        else:
            curr_borders = 0.5 * (curr_borders[0] + curr_borders[1]), curr_borders[1]
        curr_region_size /= 2

        curr_f_value = k * min(border_vals)
        curr_x_value = curr_borders[0]

    return curr_x_value, curr_f_value


def angle_equality(angle_1: Angle, angle_2: Angle) -> bool:
    return abs(angle_1.angle_mpi2_ppi2 - angle_2.angle_mpi2_ppi2) < ANGLE_EQUAL_PRECISION


def coord_equality(coord_1: float, coord_2: float, coord_precision: float = None) -> bool:
    if not coord_precision:
        coord_precision = COORD_EQUAL_PRECISION
    return abs(coord_1 - coord_2) < coord_precision


def evaluate_vector(pnt_1: Point2D, pnt_2: Point2D) -> (Angle, bool):
    """returns angle and if direction from pnt_1 to pnt_2 is positive"""
    coord_eq_prec = COORD_EQUAL_PRECISION
    max_cycle_count = 5
    while True:
        if not max_cycle_count:
            raise ValueError('Given points are equal')
        max_cycle_count -= 1
        if coord_equality(pnt_1.y, pnt_2.y, coord_eq_prec) and coord_equality(pnt_1.x, pnt_2.x, coord_eq_prec):
            coord_eq_prec *= COORD_EQUAL_PRECISION
        else:
            break
    if coord_equality(pnt_1.y, pnt_2.y, coord_eq_prec):
        if ANGLE_EQUAL_PRECISION * abs(pnt_1.x - pnt_2.x) > abs(pnt_1.y - pnt_2.y):
            return Angle(0), pnt_2.x > pnt_1.x
    if coord_equality(pnt_1.x, pnt_2.x, coord_eq_prec):
        if ANGLE_EQUAL_PRECISION * abs(pnt_1.y - pnt_2.y) > abs(pnt_1.x - pnt_2.x):
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
    assert line_1.angle != line_2.angle, 'Angles of lines are equal'
    result = np.linalg.solve(np.array([[line_1.a, line_1.b], [line_2.a, line_2.b]]), np.array([-line_1.c, -line_2.c]))
    return Point2D(result[0], result[1])


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


def bezier_curvature(t: Real, pnt_1: Point2D, pnt_2: Point2D, pnt_control: Point2D):
    x1, y1 = pnt_1.coords
    x2, y2 = pnt_2.coords
    x3, y3 = pnt_control.coords
    return abs(0.5 * (-(2 * (x3 - x1) + x1 - x2) * (2 * (y3 - y1) * t - (y3 - y1) + t * y1 - t * y2) +
                      (2 * (y3 - y1) + y1 - y2) * (2 * (x3 - x1) * t - (x3 - x1) + t * x1 - t * x2)) *
               ((2 * (x3 - x1) * t - (x3 - x1) + t * x1 - t * x2) ** 2 + (
                       2 * (y3 - y1) * t - (y3 - y1) + t * y1 - t * y2) ** 2) ** (-1.5))


class Angle:
    # ! angle is measured clockwise
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
            return abs(self.angle_mpi2_ppi2 - other) < ANGLE_EQUAL_PRECISION
        else:
            return abs(self.angle_mpi2_ppi2 - other.angle_mpi2_ppi2) < ANGLE_EQUAL_PRECISION

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def angle_0_2pi(self):
        # radian value in interval [0, 2pi)
        positive_angle = self.free_angle % (2 * math.pi)
        return positive_angle

    @property
    def deg_angle_0_360(self):
        # degree value in interval [0, 360)
        return self.angle_0_2pi * 180 / math.pi

    @property
    def angle_mpi2_ppi2(self):
        # radian value in interval (-pi/2, pi/2]
        positive_angle = self.free_angle % math.pi
        return positive_angle - math.pi if positive_angle > math.pi / 2 else positive_angle

    @property
    def deg_angle_m90_p90(self):
        # degree value in interval (-90, 90]
        return self.angle_mpi2_ppi2 * 180 / math.pi


class Line2D:
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D = None, angle: Angle = None):
        # Line is solution of equation a*x + b*y + c = 0
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


class Rect:
    def __init__(self, x: Union[Real, Point2D] = None, y: Union[Real, Angle] = None, w: Real = None, h: Real = None,
                 center: Point2D = None, angle: Angle = None):
        """ docstring """
        if type(x) == Point2D:
            center = x
            angle = y
            x = None
            y = None
        assert not (w is None) & (not (h is None)), 'Width and height should be defined'
        assert ((not (x is None)) & (not (y is None)) & (angle is None)) | \
               ((not (center is None)) & (not (angle is None))), 'Not complete input data'

        if angle is None:
            angle = Angle(0)
        if not (x is None):
            self.center = Point2D(float(x + w / 2), float(y + h / 2))
            self.angle = Angle(0)
        else:
            self.center = center
            self.angle = angle
        self.center: Point2D
        self.angle: Angle
        self.w = w
        self.h = h

    def includes_point(self, p: Point2D):
        # border includes points too
        rot_point = rotate_operation(self.center, p, Angle(-self.angle.free_angle))
        print('rot_point', rot_point)
        return (self.center.x - self.w / 2 <= rot_point.x <= self.center.x + self.w / 2) & \
               (self.center.y - self.h / 2 <= rot_point.y <= self.center.y + self.h / 2)


class GeometryPrimitive(ABC):

    @abstractmethod
    def draw_parameters(self):
        pass


# class LineSegment(GeometryPrimitive):
#     def __init__(self, pnt_1: Point2D, pnt_2: Point2D):
#         self.pnt_1 = pnt_1
#         self.pnt_2 = pnt_2
#
#     def draw_parameters(self):
#         pass


class BoundedCurve(GeometryPrimitive):
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D, angle_1: Angle = None, angle_2: Angle = None):
        self.pnt_1 = pnt_1
        self.pnt_2 = pnt_2
        if angle_1 is None and angle_2 is None:
            self.geom_type = BSSCurveType('line_segment')
        elif angle_2 is None:
            self.geom_type = BSSCurveType('optimal_bezier')
            self.angle_1 = angle_1
        else:
            self.geom_type = BSSCurveType('bezier')
            self.angle_1 = angle_1
            self.angle_2 = angle_2
        if self.geom_type != 'line_segment':
            self.check_not_on_line()
        if self.geom_type == 'optimal_bezier':
            self.angle_2 = self.bezier_optimization()

    def check_not_on_line(self):
        angle_between = Line2D(self.pnt_1, self.pnt_2).angle
        if self.angle_1 == angle_between:
            self.geom_type = BSSCurveType('line_segment')
        if (self.geom_type == 'bezier') and (self.angle_2 == angle_between):
            self.geom_type = BSSCurveType('line_segment')

    def bezier_control_point(self) -> Point2D:
        return lines_intersection(Line2D(self.pnt_1, angle=self.angle_1), Line2D(self.pnt_2, angle=self.angle_2))

    def bezier_optimization(self) -> Angle:
        float_angle_1 = self.angle_1.angle_mpi2_ppi2
        return Angle(cut_optimization(self.max_curvature,
                                      borders=(float_angle_1 + 1e3 * ANGLE_EQUAL_PRECISION,
                                               float_angle_1 + math.pi - 1e3 * ANGLE_EQUAL_PRECISION))[0])

    def max_curvature(self, float_angle: float) -> float:
        angle = Angle(float_angle)
        pnt_intersect = lines_intersection(Line2D(self.pnt_1, angle=self.angle_1), Line2D(self.pnt_2, angle=angle))
        return cut_optimization(bezier_curvature, self.pnt_1, self.pnt_2, pnt_intersect,
                                borders=(0, 1), maxormin=BSSMaxMin('max'))[1]

    def draw_parameters(self):
        if self.geom_type == 'line_segment':
            return 'line_segment', *self.pnt_1.coords, *self.pnt_2.coords
        else:
            return 'bezier', *self.pnt_1.coords, *self.bezier_control_point().coords, *self.pnt_2.coords


class Ellipse(GeometryPrimitive):
    def __init__(self):
        pass

    def draw_parameters(self):
        pass


class FrameCS:
    # CS in Frame
    def __init__(self, base_cs: FrameCS = None, center_pnt_in_base: Point2D = Point2D(0, 0),
                 scale_in_base_x: Real = 1, scale_in_base_y: Real = 1):
        self._base_cs = base_cs
        self._center_pnt_in_base = center_pnt_in_base
        # scale > 1 means that ticks more often
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


class FramePrimitive(ABC):

    @abstractmethod
    def reevaluate(self) -> GeometryPrimitive:
        pass

    @abstractmethod
    def point_in_clickable_area(self, pnt: Point2D) -> bool:
        pass


class FPLineSegment(FramePrimitive):

    def reevaluate(self):
        pass

    def point_in_clickable_area(self, pnt: Point2D) -> bool:
        pass


class MainFrame:
    def __init__(self):
        self.main_frame_points = None
        self.main_frame_primitives = None


# @abstractmethod
# def display_params(self) -> list[Real]:
#     pass

#
# class LineSegment(GeomPrimitive):
#     def __init__(self, pnt_1: Point2D, pnt_2: Point2D):
#         self.pnt_1 = pnt_1
#         self.pnt_2 = pnt_2
#
#     def display_params(self):
#         return [*self.pnt_1.coords, *self.pnt_2.coords]
#
#     def point_in_clickable_area(self, p: Point2D, scale: float):
#         center = Point2D((self.pnt_1.x + self.pnt_2.x) / 2, (self.pnt_1.y + self.pnt_2.y) / 2)
#         angle, _ = evaluate_vector(self.pnt_1, self.pnt_2)
#         width = math.dist(self.pnt_1.coords, self.pnt_2.coords)
#         assert False, 'Not yet implemented'
#         return Rect(center, angle, width, )
#
#
# class Circle(GeomPrimitive):
#     def __init__(self, center: Point2D, r: Real):
#         self.center = center
#         self.r = r
#
#     def display_params(self):
#         return [*self.center.coords, self.r]
#
#     def point_in_clickable_area(self, p: Point2D, scale: float):
#         pass
#
#
# class BezierCurve(GeomPrimitive):
#     def __init__(self, pnt_1: Point2D, angle_1: Angle, pnt_2: Point2D, angle_2: Angle):
#         self.pnt_1 = pnt_1
#         self.angle_1 = angle_1
#         self.pnt_2 = pnt_2
#         self.angle_2 = angle_2
#         self.pnt_intersect = lines_intersection(Line2D(pnt_1, angle=angle_1), Line2D(pnt_2, angle=angle_2))
#
#     def display_params(self):
#         return [*self.pnt_1.coords, *self.pnt_2.coords, *self.pnt_intersect.coords]
#
#     def point_in_clickable_area(self, p: Point2D, scale: float):
#         pass


class GraphicalObject:
    def __init__(self):
        self.geom_primitives = set()


class ContinuousVisibleArea(QObject):

    def __init__(self):
        super().__init__()
        self.current_scale = 1.  # px/m
        self.upleft_x = None

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


# class IPoint:
#     def __init__(self, x0, y0, fictive=False):
#         self.fictive = fictive
#         self._x0 = x0
#         self._y0 = y0
#         self._scale = 1
#         self._x = x0
#         self._y = y0
#
#     @property
#     def x0(self):
#         return self._x0
#
#     @property
#     def y0(self):
#         return self._y0
#
#     @property
#     def x(self):
#         return self._x
#
#     @property
#     def y(self):
#         return self._y
#
#     @property
#     def scale(self):
#         return self._scale
#
#     @scale.setter
#     def scale(self, value: Real):
#         self._scale = value
#         self._x = self.x0 * value
#         self._y = self.y0 * value
#
#
# class IPrimitive(ABC):
#     def __init__(self, pnt_1: IPoint, pnt_2: IPoint):
#         self.weight = 1
#         self.color = 'black'
#         self.dashed = False
#         self.pnt_1 = pnt_1
#         self.pnt_2 = pnt_2
#
#     @abstractmethod
#     def re_evaluate(self):
#         pass
#
#
# class ILine(IPrimitive):
#     def __init__(self, pnt_1: IPoint, pnt_2: IPoint):
#         super().__init__(pnt_1, pnt_2)
#
#     def re_evaluate(self):
#         pass
#
#
# class ISimpleBezier(IPrimitive):
#     def __init__(self, pnt_1: IPoint, pnt_2: IPoint, ang_1: Angle, ang_2: Angle):
#         super().__init__(pnt_1, pnt_2)
#         self.ang_1 = ang_1
#         self.ang_2 = ang_2
#
#     def re_evaluate(self):
#         pass
#
#
# class IOptimalBezier(IPrimitive):
#     def __init__(self, pnt_1: IPoint, pnt_2: IPoint, ang_1: Angle):
#         super().__init__(pnt_1, pnt_2)
#         self.ang_1 = ang_1
#
#     def re_evaluate(self):
#         pass


if __name__ == '__main__':
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

    r = Rect(Point2D(7, 5), Angle(-26.565 * math.pi / 180), 8.944, 4.472)
    print(r.includes_point(Point2D(3, 8)))

    # Point2D((6,))

    # base_cs = FrameCS()
    # center_cs = FrameCS(base_cs, Point2D(10, 20), 2, 2)
    # sec_cs = FrameCS(center_cs, Point2D(10, 20), 3, 2)
    # print(sec_cs.center_pnt_absolute_x, sec_cs.center_pnt_absolute_y, sec_cs.scale_absolute_x, sec_cs.scale_absolute_y)

    # def transform_coordinates(pnt: Point2D, cs_base: FrameCS, cs_new: FrameCS) -> Point2D:
    #     pnt_abs_x = pnt.x / cs_base.scale_absolute_x + cs_base.center_pnt_absolute_x
    #     pnt_abs_y = pnt.y / cs_base.scale_absolute_y + cs_base.center_pnt_absolute_y
    #     pnt_new_x = (pnt_abs_x - cs_new.center_pnt_absolute_x) * cs_new.scale_absolute_x
    #     pnt_new_y = (pnt_abs_y - cs_new.center_pnt_absolute_y) * cs_new.scale_absolute_y
    #     return Point2D(pnt_new_x, pnt_new_y)
    #     print(transform_coordinates(Point2D(3, 2), center_cs, sec_cs))

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


    def max_curvature(float_angle: float):
        angle = Angle(float_angle)
        pnt_1 = Point2D(1, 1)
        angle_1 = Angle(math.pi / 4)
        pnt_2 = Point2D(3, 1)
        pnt_intersect = lines_intersection(Line2D(pnt_1, angle=angle_1), Line2D(pnt_2, angle=angle))
        print(pnt_intersect)
        return cut_optimization(bezier_curvature, pnt_1, pnt_2, pnt_intersect,
                                borders=(0, 1), maxormin=BSSMaxMin('max'))[1]


    # print(max_curvature(-math.pi/4))
    print(cut_optimization(max_curvature, borders=(math.pi / 4 + 0.01, math.pi + math.pi / 4 - 0.01)))
    print(Angle(2.3561937459466598).deg_angle_0_360)
    # print(bezier_curvature(0.0, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
    # print(bezier_curvature(0.2, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
    # print(bezier_curvature(0.4, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
    # print(bezier_curvature(0.6, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
    # print(bezier_curvature(0.8, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))
    # print(bezier_curvature(1.0, Point2D(1, 1), Point2D(3, 1), Point2D(2.0, 2.0)))

    bc = BoundedCurve(Point2D(1, 1), Point2D(3, 1))
    bc_2 = BoundedCurve(Point2D(1, 1), Point2D(3, 1), Angle(math.pi/4), Angle(math.pi/2))
    bc_3 = BoundedCurve(Point2D(1, 1), Point2D(3, 1), Angle(math.pi/4))
    print(bc.draw_parameters())
    print(bc_2.draw_parameters())
    print(bc_3.draw_parameters())

