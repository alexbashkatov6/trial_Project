from __future__ import annotations

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject


class CommandSupervisor(QObject):
    def __init__(self):
        super(CommandSupervisor, self).__init__()
