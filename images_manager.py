from __future__ import annotations
from collections import OrderedDict

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from nv_config import CLASSES_SEQUENCE


class ImgBuilder:
    def __init__(self, manager: ImagesManager):
        self.mng = manager

    def copy_obj(self):
        pass


class ImgValidator:
    def __init__(self, manager: ImagesManager):
        """
        Main idea is use built-in Python interpreter for string evaluations
        """
        self.mng = manager

    def validate_value(self):
        pass


class ImgCommandSupervisor:
    def __init__(self, manager: ImagesManager):
        """
        Undo commands for command:
        create([obj_1, obj_2, ...]) <-> delete([obj_1, obj_2, ...])
        edit(obj -> e_obj) <-> edit(e_obj -> obj)
        """
        self.mng = manager
        self.redo_commands = []
        self.undo_commands = []


class ImgDependenceGraph:
    def __init__(self, manager: ImagesManager):
        """
        Batch execution:
        virtual_builtin -> linearize -> validate_img
        """
        self.mng = manager
        self.clean_dg = None

    def virtual_builtin(self):
        pass

    def linearize(self):
        pass

    def validate_img(self):
        pass

    def read_from_file(self):
        pass

    def dump_to_file(self):
        pass


class ImgTreeView(QObject):
    def __init__(self, manager: ImagesManager):
        super().__init__()
        self.mng = manager


class ImgAttribView(QObject):
    def __init__(self, manager: ImagesManager):
        super().__init__()
        self.mng = manager


class ImagesManager:
    def __init__(self):
        self.tree_view = ImgBuilder(self)
        self.attrib_view = ImgAttribView(self)

        self.builder = ImgBuilder(self)
        self.validator = ImgValidator(self)
        self.dg = ImgDependenceGraph(self)
        self.comm_sup = ImgCommandSupervisor(self)
