from __future__ import annotations
import math
import numpy as np
from typing import Union
from numbers import Real
from nv_config import ANGLE_EQUAL_PRECISION, COORD_EQUAL_PRECISION


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


class Angle:
    def __init__(self, free_angle: Real):
        # value returned by angle should be in interval (-pi/2, pi/2]
        self.free_angle = float(free_angle)

    @property
    def angle(self):
        positive_angle = self.free_angle % math.pi
        return positive_angle-math.pi if positive_angle > math.pi/2 else positive_angle

    @property
    def deg_angle(self):
        return self.angle*180/math.pi


def angle_equality(angle_1: Angle, angle_2: Angle) -> bool:
    return abs(angle_1.angle-angle_2.angle) < ANGLE_EQUAL_PRECISION


def coord_equality(coord_1: float, coord_2: float, coord_precision: float = None) -> bool:
    if not coord_precision:
        coord_precision = COORD_EQUAL_PRECISION
    return abs(coord_1-coord_2) < coord_precision


def evaluate_line_angle(pnt_1: Point2D, pnt_2: Point2D) -> Angle:
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
            return Angle(0)
    if coord_equality(pnt_1.x, pnt_2.x, coord_eq_prec):
        if ANGLE_EQUAL_PRECISION * abs(pnt_1.y - pnt_2.y) > abs(pnt_1.x - pnt_2.x):
            return Angle(math.pi/2)
    return Angle(math.atan((pnt_1.y - pnt_2.y)/(pnt_1.x - pnt_2.x)))


def rotate_operation(point: Point2D, center: Point2D, angle: Angle) -> Point2D:
    return center


class Line2D:
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D = None, angle: Angle = None):
        # Line is solution of equation a*x + b*y + c = 0
        #
        assert not(pnt_2 is None) or not(angle is None), 'Not complete input data'
        self.pnt = pnt_1
        if angle:
            self.angle = angle
        else:
            self.angle = evaluate_line_angle(pnt_1, pnt_2)
        self.a, self.b, self.c = None, None, None
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
        self.a = -math.sin(self.angle.angle)
        self.b = math.cos(self.angle.angle)
        self.c = -self.a * self.pnt.x - self.b * self.pnt.y



class Segment2D:
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D):
        pass


class BezierCurve:
    pass


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
        pass


class GraphicalObject:
    def __init__(self):
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
    print(a.angle)
    print(evaluate_line_angle(Point2D(1e-7, 0), Point2D(0, 0)).deg_angle)
    line = Line2D(Point2D(0, 1), Point2D(3, 2))
    print(line.a, line.b, line.c)
