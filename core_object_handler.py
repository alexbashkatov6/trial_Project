from __future__ import annotations

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject


class CoreObjectHandler(QObject):
    obj_created = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        pass

    @pyqtSlot(dict)
    def got_obj_created(self, obj_info: dict):
        print('got obj_created in COH', obj_info)
        self.obj_created.emit(obj_info)
