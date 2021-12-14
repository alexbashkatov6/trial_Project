from __future__ import annotations

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from nv_config import GROUND_CS_NAME
from nv_attributed_objects import CoordinateSystem, GroundLine, Point, Line  # AttrControlObject,

'''
name

CoordinateSystem
cs_relative_to
dependence 'dependent' 'independent'
x
y
alpha
connection_polarity 'negative_down' 'positive_up'
co_x 'True' 'False'
co_y 'True' 'False'

GroundLine
cs_relative_to
move_method 'translational' 'rotational'
y
center_point
alpha

Point
cs_relative_to
on_line_or_ground_line
x
ground_line
line

Line
first_point
second_point
'''


class EvaluationCS:
    def __init__(self, base_cs: EvaluationCS = None, co_x: bool = True, x: int = 0):
        self._base_cs = base_cs
        self._is_base = base_cs is None
        self._in_base_x = x
        self._in_base_co_x = co_x

        self._absolute_x = 0
        self._absolute_co_x = True
        self.eval_absolute_parameters()

    @property
    def is_base(self):
        return self._is_base

    @property
    def base_cs(self):
        return self._base_cs

    @property
    def in_base_x(self):
        return self._in_base_x

    @property
    def in_base_co_x(self):
        return self._in_base_co_x

    @property
    def absolute_x(self) -> int:
        return self._absolute_x

    @property
    def absolute_co_x(self) -> bool:
        return self._absolute_co_x

    def eval_absolute_parameters(self):
        if not self.is_base:
            self._absolute_x = self.base_cs.absolute_x + self.in_base_x
            self._absolute_co_x = self.base_cs.absolute_co_x == self.in_base_co_x


class CoreObjectHandler(QObject):
    obj_created = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.cs_dict = {}

    @pyqtSlot(dict)
    def got_obj_created(self, obj_info: dict):
        print('got obj_created in COH', obj_info)
        self.obj_created.emit(obj_info)
        obj = list(obj_info.keys())[0]
        if isinstance(obj, CoordinateSystem):
            self.new_cs_handler(obj)
        elif isinstance(obj, GroundLine):
            self.new_ground_line_handler(obj)
        elif isinstance(obj, Point):
            self.new_point_handler(obj)
        elif isinstance(obj, Line):
            self.new_line_handler(obj)

    def obj_changed(self, obj_info: dict):
        pass

    def new_cs_handler(self, cs):
        print("in new_cs_handler")
        if cs.dependence == 'dependent':
            eCS = EvaluationCS()

    def new_ground_line_handler(self, gl):
        print("in new_ground_line_handler")

    def new_point_handler(self, pnt):
        print("in new_point_handler")

    def new_line_handler(self, ln):
        print("in new_line_handler")
