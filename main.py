import sys
import traceback

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject

from new_main_window import MW
from adapter_core_to_pyqt_interface import AdapterCorePyqtInterface


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Oбнаружена ошибка !:", tb)


sys.excepthook = excepthook


class Director(QObject):
    def __init__(self):
        super().__init__()
        self.mw = MW()
        self.acpi = AdapterCorePyqtInterface()

        self.mw.config_directory_selected.connect(self.acpi.read_station_config)
        self.mw.undo.connect(self.acpi.undo)
        self.mw.redo.connect(self.acpi.redo)
        self.mw.eval_routes_directory_selected.connect(self.acpi.eval_routes)

        self.mw.ttb.send_class_name.connect(self.acpi.create_new_object)

        self.acpi.send_cls_obj_dict.connect(self.mw.ltb.tree_view.from_dict)
        self.mw.ltb.tree_view.send_obj_double_clicked.connect(self.acpi.change_current_object)
        self.mw.ltb.tree_view.send_add_new.connect(self.acpi.create_new_object)
        self.mw.ltb.tree_view.send_attrib_request.connect(self.acpi.change_current_object)
        self.mw.ltb.tree_view.send_delete_request.connect(self.acpi.delete_request)
        self.acpi.send_delete_names.connect(self.mw.deletion_warning)
        self.mw.deletion_confirmed.connect(self.acpi.delete_confirmed)

        # --------------------  old rows  -------------------- #

        # from nv_attributed_objects import CommonAttributeInterface
        # from graphical_object import Frame, BaseFrame
        # from core_object_handler import CoreObjectHandler

        # self.cai = CommonAttributeInterface()
        # self.coh = CoreObjectHandler()  #
        # self.pfr = BaseFrame()  # PatternFrame
        # self.cfr = Frame(self.pfr)  # CaptureFrame

        # interface to attr_object storage
        # self.mw.ttb.send_class_name.connect(self.cai.create_new_object)
        # self.mw.rtb.new_name_value_tb.connect(self.cai.slot_change_value)
        # self.mw.rtb.apply_clicked.connect(self.cai.apply_changes)
        # self.mw.ltb.send_data_hover.connect(self.cai.hover_handling)
        # self.mw.ltb.send_data_pick.connect(self.cai.pick_handling)
        # self.mw.ltb.send_data_edit.connect(self.cai.change_current_object)
        # self.mw.ltb.send_leave.connect(self.cai.reset_tree_handling)

        # attr_object storage to interface
        # self.cai.send_attrib_list.connect(self.mw.rtb.set_attr_struct)
        # self.cai.send_class_str.connect(self.mw.rtb.set_class_str)
        # self.cai.create_readiness.connect(self.mw.rtb.set_active_apply)
        # self.cai.new_str_tree.connect(self.mw.ltb.set_tree)
        # self.cai.send_info_object.connect(self.mw.ltb.show_info_about_object)

        # interface to visible_area
        # self.mw.pa.pa_coordinates_changed.connect(self.pfr.pa_coordinates_changed)
        # self.mw.pa.zoom_in_selection_coordinates.connect(self.pfr.zoom_in_selection_coordinates)
        # self.mw.pa.zoom_out_selection_coordinates.connect(self.pfr.zoom_out_selection_coordinates)

        # internal interface connections
        # self.mw.ltb.send_data_fill.connect(self.mw.rtb.set_focus_widget_value)

        # obj creation connections
        # self.cai.obj_created.connect(self.coh.got_obj_created)
        # self.coh.obj_created.connect(self.pfr.got_obj_created)

        # initialization
        # self.cai.get_tree_graph()
        # self.mw.pa.init_resize()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())
