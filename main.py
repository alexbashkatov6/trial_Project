import sys
import traceback

from main_window import MW
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject
from messages import MessagesManager
from nv_attributed_objects import CommonAttributeInterface


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Oбнаружена ошибка !:", tb)


sys.excepthook = excepthook


class Director(QObject):
    def __init__(self):
        super().__init__()
        self.mw = MW()
        self.mm = MessagesManager(self.mw)
        self.cai = CommonAttributeInterface()

        # interface to storage
        self.mw.ttb.send_class_name.connect(self.cai.create_new_object)
        self.mw.rtb.new_name_value_tb.connect(self.cai.slot_change_value)

        # storage to interface
        self.cai.send_attrib_list.connect(self.mw.rtb.set_attr_struct)
        self.cai.send_class_str.connect(self.mw.rtb.set_class_str)
        self.cai.create_readiness.connect(self.mw.rtb.set_active_apply)
        self.cai.send_single_value.connect(self.mw.rtb.replace_line_edit)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())
