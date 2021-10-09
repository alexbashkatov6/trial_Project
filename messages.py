from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSlot


class MessagesManager(QObject):
    def __init__(self, mw):
        super().__init__()
        self.mw = mw

    @pyqtSlot(str)
    def info_message(self, val):
        QMessageBox.about(self.mw, "Title", val)