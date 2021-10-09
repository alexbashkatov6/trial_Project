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

        self.mw.ttb.sendClassName.connect(self.cai.create_new_object)
        self.cai.send_attrib_list.connect(self.mw.rtb.set_attr_struct)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())
