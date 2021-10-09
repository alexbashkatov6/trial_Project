import sys

from main_window import MW
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject
from messages import MessagesManager
from nv_attributed_objects import CommonAttributeInterface


class Director(QObject):
    def __init__(self):
        super().__init__()
        self.mw = MW()
        self.mm = MessagesManager(self.mw)
        self.cai = CommonAttributeInterface()

        self.set_connections()

    def set_connections(self):
        self.mw.ttb.sendClassName.connect(self.mw.ce.setClassName)
        self.mw.ce.sendClassNameStr.connect(self.mw.rtb.setClassName)
        self.mw.ce.sendAttribsStructure.connect(self.mw.rtb.setAttrStruct)
        # print(self.cai)
        self.mw.ttb.sendClassName.connect(self.cai.create_new_object)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())
