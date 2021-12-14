from __future__ import annotations

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from nv_config import GROUND_CS_NAME
from nv_attributed_objects import CoordinateSystem, GroundLine, Point, Line  # AttrControlObject,

'''
name

CoordinateSystem
cs_relative_to
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
x
ground_line
line

Line
first_point
second_point
'''


class CoreObjectHandler(QObject):
    obj_created = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        pass

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

    def new_cs_handler(self, obj):
        print("in new_cs_handler")
        for attr in obj.__dict__:
            print("attr", attr)
        print('cox', type(obj.co_x))

    def new_ground_line_handler(self, obj):
        print("in new_ground_line_handler")

    def new_point_handler(self, obj):
        print("in new_point_handler")

    def new_line_handler(self, obj):
        print("in new_line_handler")

