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

        # interface to storage
        self.mw.ttb.sendClassName.connect(self.cai.create_new_object)
        self.mw.rtb.new_name_value_tb.connect(self.cai.slot_change_value)

        # storage to interface
        self.cai.send_attrib_list.connect(self.mw.rtb.set_attr_struct)
        self.cai.send_class_str.connect(self.mw.rtb.set_class_str)
        self.cai.create_readiness.connect(self.mw.rtb.set_active_apply)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())
