from __future__ import annotations
from typing import Optional

from graphical_object import Point2D, Line2D, BoundedCurve
from enums_images import CELightRouteType, CELightColor, CELightStickType, CEBorderType, CESectionType


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
