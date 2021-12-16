from __future__ import annotations
from collections import OrderedDict

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from nv_config import CLASSES_SEQUENCE


class CommandSupervisor:
    def __init__(self):
        pass


class DependenceGraph:
    def __init__(self):
        pass


class ImagesTreeView(QObject):
    def __init__(self):
        super().__init__()


class ImagesStorage:
    def __init__(self):
        self._clear_storage = None
        self._dirty_storage = None
        self.init_storages()
        self.cs = CommandSupervisor()
        self.dg = DependenceGraph()
        self.itv = ImagesTreeView()

    def init_storages(self):
        self._clear_storage = OrderedDict()
        self._dirty_storage = OrderedDict()

    def read_from_file(self):
        pass

    def dump_to_file(self):
        pass