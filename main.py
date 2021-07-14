# import engine_core as ec
from main_window import Example
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject


class Director(QObject):
    def __init__(self):
        super().__init__()
        self.ex = Example()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())


