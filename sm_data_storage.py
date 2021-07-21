from sm_objs_inspector import ObjsInspector

from PyQt5.QtCore import QObject

OI = ObjsInspector()


class DataStorage(QObject):
    def __init__(self):
        super().__init__()

