from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject

class MessagesManager(QObject):
    def __init__(self):
        super().__init__()

    def infoMessage(self):
        print('OK')