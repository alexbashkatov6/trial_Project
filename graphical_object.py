import math
from numbers import Number


class Point2D:
    def __init__(self, x: Number = None, y: Number = None, c: tuple = None):
        if type(x) == tuple:
            c = x
            x = None
            y = None
        assert ((not(x is None)) & (not(y is None))) | (not(c is None)), 'Not complete input data'
        if x:
            self.x = x
            self.y = y
        else:
            self.x = c[0]
            self.y = c[1]


class Line2D:
    def __init__(self, pnt_1: Point2D, pnt_2: Point2D):
        pass


def rotate_operation(point: Point2D, center: Point2D, angle: Number) -> Point2D:
    angle = float(angle)


class Rect:
    def __init__(self, x: Number = None, y: Number = None, w: Number = None, h: Number = None,
                 center: tuple = None, angle: Number = None):
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
