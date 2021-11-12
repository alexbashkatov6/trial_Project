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
        self.mw.rtb.apply_clicked.connect(self.cai.apply_changes)
        self.mw.ltb.send_data_hover.connect(self.cai.hover_handling)
        self.mw.ltb.send_data_pick.connect(self.cai.pick_handling)
        self.mw.ltb.send_data_edit.connect(self.cai.change_current_object)
        self.mw.ltb.send_leave.connect(self.cai.reset_tree_handling)

        # storage to interface
        self.cai.send_attrib_list.connect(self.mw.rtb.set_attr_struct)
        self.cai.send_class_str.connect(self.mw.rtb.set_class_str)
        self.cai.create_readiness.connect(self.mw.rtb.set_active_apply)
        self.cai.new_str_tree.connect(self.mw.ltb.set_tree)
        self.cai.send_info_object.connect(self.mw.ltb.show_info_about_object)

        # internal interface connections
        self.mw.ltb.send_data_fill.connect(self.mw.rtb.set_focus_widget_value)

        # initialization
        self.cai.get_tree_graph()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())
