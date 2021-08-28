from __future__ import annotations
from nv_typing import *
from numbers import Number

from nv_instances_control import instances_control



class FieldCoord:
    @strictly_typed
    def __init__(self, value: Number, cs: CoordinateSystem) -> None:
        self.value = value
        self.cs = cs


@instances_control
class CoordinateSystem:
    pass


class OneOf:
    pass
