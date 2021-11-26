from __future__ import annotations
import math
import numpy as np
from abc import ABC, abstractmethod
from typing import Union
from numbers import Real

from nv_config import ANGLE_EQUAL_PRECISION, COORD_EQUAL_PRECISION


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
    def __init__(self, x: Union[Real, tuple] = None, y: Real = None, c: tuple = None, line: Line2D = None):
        if type(x) == tuple:
            c = x
            x = None
            y = None
        assert ((not(x is None)) & (not(y is None))) | (not(c is None)), 'Not complete input data'
        if not (x is None):
            self.x = float(x)
            self.y = float(y)
        else:
            self.x = float(c[0])
            self.y = float(c[1])
        if line:
            self.line = line

    @property
    def coords(self):
        return self.x, self.y


class Angle:
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
        self.eval_abc()

    def eval_abc(self):
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
        self.a = -math.sin(self.angle.angle_mpi2_ppi2)
        self.b = math.cos(self.angle.angle_mpi2_ppi2)
        self.c = -self.a * self.pnt.x - self.b * self.pnt.y


class Rect:
    def __init__(self, x: Union[Real, tuple] = None, y: Real = None, w: Real = None, h: Real = None,
                 center: tuple = None, angle: Real = None):
        """ docstring """
        if type(x) == tuple:
            center = x
            angle = y
            x = None
            y = None
        assert not (w is None) & (not(h is None)), 'Width and height should be defined'
        assert ((not(x is None)) & (not(y is None)) & (not(w is None)) & (not(h is None)) & (angle is None)) |\
               ((not(center is None)) & (not(w is None)) & (not(h is None))), 'Not complete input data'
        if angle is None:
            angle = 0.
        if x:
            self.center = (float(x+w/2), float(y+h/2))
            self.angle = 0.
        else:
            self.center = (float(center[0]), float(center[1]))
            self.angle = float(angle)
        self.w = w
        self.h = h

    def includesPoint(self, p: Point2D):
        # border too includes points
        pass


class GeomPrimitive(ABC):

    @abstractmethod
    def display(self):
        pass

    @abstractmethod
    def clickable_area(self):
        pass


class Segment2D(GeomPrimitive):
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D):
        pass

    def display(self):
        pass

    def clickable_area(self):
        pass


class Circle(GeomPrimitive):
    def __init__(self, center: Point2D, r: float):
        pass

    def display(self):
        pass

    def clickable_area(self):
        pass


class BezierCurve(GeomPrimitive):
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D):
        pass

    def display(self):
        pass

    def clickable_area(self):
        pass


class GraphicalObject:
    def __init__(self):
        pass


class Field:
    pass


class ContinuousVisibleArea:
    pass
    # H_CLICK
    # scale_from_field


class DiscreteVisibleArea:
    pass


if __name__ == '__main__':
    p1 = Point2D(10, 20)
    print('p1 x y = ', p1.x, p1.y)
    p2 = Point2D((12, 13))
    print('p2 x y = ', p2.x, p2.y)
    r1 = Rect(10, 20, 300, 400)
    print('r1 center angle = ', r1.center, r1.angle, r1.w, r1.h)
    r2 = Rect(w=10, h=20, center=(300, 400))
    print('r2 center angle = ', r2.center, r2.angle, r2.w, r2.h)
    r3 = Rect((300, 400), 0, 10, 20)
    print('r3 center angle = ', r3.center, r3.angle, r3.w, r3.h)
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
