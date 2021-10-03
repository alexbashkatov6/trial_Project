from main_window import MW
from sm_data_storage import DataStorage
from messages import MessagesManager
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject


class Director(QObject):
    def __init__(self):
        super().__init__()
        self.mw = MW()
        self.ds = DataStorage()
        self.mm = MessagesManager(self.mw)
        self.set_connections()

    def set_connections(self):
        self.mw.ttb.sendClassName.connect(self.mw.ce.setClassName)
        self.mw.ce.sendClassNameStr.connect(self.mw.rtb.setClassName)
        self.mw.ce.sendAttribsStructure.connect(self.mw.rtb.setAttrStruct)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())
