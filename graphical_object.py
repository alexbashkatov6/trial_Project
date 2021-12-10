from __future__ import annotations
import math
import numpy as np
from abc import ABC, abstractmethod
from typing import Union
from numbers import Real

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from nv_config import ANGLE_EQUAL_PRECISION, COORD_EQUAL_PRECISION, H_CLICK_ZONE
from nv_bounded_string_set_class import bounded_string_set

BSSPrimitiveType = bounded_string_set('BSSPrimitiveType', [['line_segment'], ['circle'], ['bezier']])


def angle_equality(angle_1: Angle, angle_2: Angle) -> bool:
    return abs(angle_1.angle_mpi2_ppi2 - angle_2.angle_mpi2_ppi2) < ANGLE_EQUAL_PRECISION


def coord_equality(coord_1: float, coord_2: float, coord_precision: float = None) -> bool:
    if not coord_precision:
        coord_precision = COORD_EQUAL_PRECISION
    return abs(coord_1-coord_2) < coord_precision


def evaluate_vector(pnt_1: Point2D, pnt_2: Point2D) -> (Angle, bool):
    # returns angle and if direction from pnt_1 to pnt_2 is positive
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
            return Angle(math.pi/2), pnt_2.y > pnt_1.y
    return Angle(math.atan((pnt_1.y - pnt_2.y)/(pnt_1.x - pnt_2.x))), pnt_2.x > pnt_1.x


def rotate_operation(center: Point2D, point: Point2D, angle: Angle) -> Point2D:
    current_angle, direction_is_positive = evaluate_vector(center, point)
    if not direction_is_positive:
        current_angle += math.pi
    new_angle = current_angle + angle.angle_0_2pi
    r = math.dist(point.coords, center.coords)
    return Point2D(center.x+r*math.cos(new_angle.angle_0_2pi), center.y+r*math.sin(new_angle.angle_0_2pi))


def lines_intersection(line_1: Line2D, line_2: Line2D) -> Point2D:
    assert not angle_equality(line_1.angle, line_2.angle), 'Angles of lines are equal'
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
        # self.xr = self.x
        # self.yr = self.y

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.x, self.y)

    __str__ = __repr__

    @property
    def coords(self):
        return self.x, self.y

    # def apply_transposition(self, tr: LinearTransposition):
    #     pass
    #
    # def reset_transposition(self):
    #     self.xr = self.x
    #     self.yr = self.y


class FrCS:
    # CS in Frame
    def __init__(self, base_cs: FrCS = None, center_pnt: Point2D = Point2D(0, 0),
                 scale_x: Real = 1, scale_y: Real = 1):
        if base_cs is None:
            self.is_base = True
        else:
            self.is_base = False
        self.base_cs = base_cs
        self._center_pnt = center_pnt
        self._scale_x = scale_x
        self._scale_y = scale_y
        self._transformation = np.array([[0, 0], [1, 1]])
        # center_x center_y
        #

    @property
    def center_pnt(self):
        return self._center_pnt

    @center_pnt.setter
    def center_pnt(self, value):
        self._center_pnt = value


class FrPoint:
    # Point in Frame
    def __init__(self, cs: FrCS, pnt: Point2D):
        self.cs = cs
        self.pnt = pnt

    def coords_in_cs(self, cs: FrCS):
        pass

    def coords_in_base(self):
        pass


class Frame:
    def __init__(self):
        self.corn_cs = None
        self.cent_cs = None
        self.w = None
        self.h = None


class Pattern(Frame):
    def __init__(self):
        super().__init__()


class Capture(Frame):
    def __init__(self):
        super().__init__()


# class LinearTransposition:
#     def __init__(self, center: Point2D, scale: Real):
#         self.center = center
#         self.scale = float(scale)
#
#     def apply_to_point(self, pnt: Point2D) -> tuple[float, float]:
#         new_x = self.center.x + (pnt.x - self.center.x) * self.scale
#         new_y = self.center.y + (pnt.y - self.center.y) * self.scale


class Angle:
    # ! angle is measured clockwise
    def __init__(self, free_angle: Real):
        self.free_angle = float(free_angle)

    def __add__(self, other):
        assert isinstance(other, (Real, Angle)), 'Can add only angle or int/float'
        if isinstance(other, Real):
            return Angle(self.free_angle+other)
        else:
            return Angle(self.free_angle + other.free_angle)

    @property
    def angle_0_2pi(self):
        # radian value in interval [0, 2pi)
        positive_angle = self.free_angle % (2*math.pi)
        return positive_angle

    @property
    def deg_angle_0_360(self):
        # degree value in interval [0, 360)
        return self.angle_0_2pi * 180 / math.pi

    @property
    def angle_mpi2_ppi2(self):
        # radian value in interval (-pi/2, pi/2]
        positive_angle = self.free_angle % math.pi
        return positive_angle-math.pi if positive_angle > math.pi/2 else positive_angle

    @property
    def deg_angle_m90_p90(self):
        # degree value in interval (-90, 90]
        return self.angle_mpi2_ppi2 * 180 / math.pi


class Line2D:
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D = None, angle: Angle = None):
        # Line is solution of equation a*x + b*y + c = 0
        assert not(pnt_2 is None) or not(angle is None), 'Not complete input data'
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
        if angle_equality(self.angle, Angle(0)):
            self.a = 0
            self.b = 1
            self.c = -self.pnt.y
            return
        if angle_equality(self.angle, Angle(math.pi/2)):
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
        assert not (w is None) & (not(h is None)), 'Width and height should be defined'
        assert ((not(x is None)) & (not(y is None)) & (angle is None)) | \
               ((not(center is None)) & (not (angle is None))), 'Not complete input data'

        if angle is None:
            angle = Angle(0)
        if not (x is None):
            self.center = Point2D(float(x+w/2), float(y+h/2))
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
        return (self.center.x - self.w/2 <= rot_point.x <= self.center.x + self.w/2) & \
               (self.center.y - self.h/2 <= rot_point.y <= self.center.y + self.h/2)


class GeomPrimitive(ABC):

    @abstractmethod
    def display_params(self) -> list[Real]:
        pass

    @abstractmethod
    def point_in_clickable_area(self, p: Point2D, scale: float) -> bool:
        pass


class LineSegment(GeomPrimitive):
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D):
        self.pnt_1 = pnt_1
        self.pnt_2 = pnt_2

    def display_params(self):
        return [*self.pnt_1.coords, *self.pnt_2.coords]

    def point_in_clickable_area(self, p: Point2D, scale: float):
        center = Point2D((self.pnt_1.x + self.pnt_2.x)/2, (self.pnt_1.y + self.pnt_2.y)/2)
        angle, _ = evaluate_vector(self.pnt_1, self.pnt_2)
        width = math.dist(self.pnt_1.coords, self.pnt_2.coords)
        assert False, 'Not yet implemented'
        return Rect(center, angle, width, )


class Circle(GeomPrimitive):
    def __init__(self, center: Point2D, r: Real):
        self.center = center
        self.r = r

    def display_params(self):
        return [*self.center.coords, self.r]

    def point_in_clickable_area(self, p: Point2D, scale: float):
        pass


class BezierCurve(GeomPrimitive):
    def __init__(self, pnt_1: Point2D, angle_1: Angle, pnt_2: Point2D, angle_2: Angle):
        self.pnt_1 = pnt_1
        self.angle_1 = angle_1
        self.pnt_2 = pnt_2
        self.angle_2 = angle_2
        self.pnt_intersect = lines_intersection(Line2D(pnt_1, angle=angle_1), Line2D(pnt_2, angle=angle_2))

    def display_params(self):
        return [*self.pnt_1.coords, *self.pnt_2.coords, *self.pnt_intersect.coords]

    def point_in_clickable_area(self, p: Point2D, scale: float):
        pass


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
        print('got zoom in select coords', select_coords[0][0], select_coords[0][1], select_coords[1][0], select_coords[1][1])
        # H_CLICK_ZONE

    @pyqtSlot(tuple)
    def zoom_out_selection_coordinates(self, select_coords: tuple[tuple[int, int], tuple[int, int]]):
        print('got zoom out select coords', select_coords[0][0], select_coords[0][1], select_coords[1][0], select_coords[1][1])
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
    b = Angle(-2*math.pi+0.001)
    print(b.angle_0_2pi)
    print(math.dist((0, 0), (1, 1)))
    print(rotate_operation(Point2D(0, 0), Point2D(0, 1), Angle(math.pi/2)).coords)
    print(lines_intersection(Line2D(Point2D(0, 0), Point2D(1, 1)), Line2D(Point2D(1, 1), Point2D(2, 0))).coords)

    bc = BezierCurve(Point2D(100, 100), Angle(0), Point2D(300, 200), Angle(math.pi*0.25))
    print(bc.display_params())

    r = Rect(Point2D(7, 5), Angle(-26.565*math.pi/180), 8.944, 4.472)
    print(r.includes_point(Point2D(3, 8)))

    Point2D((6, ))
