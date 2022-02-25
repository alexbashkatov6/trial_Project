from collections import OrderedDict

from PyQt5.QtCore import QObject, pyqtSignal

from old_command_supervisor import CommandSupervisor
from default_ordered_dict import DefaultOrderedDict


class AdapterCorePyqtInterface(QObject):
    """ blind commander """
    send_cls_obj_dict = pyqtSignal(OrderedDict)
    send_delete_names = pyqtSignal(list)
    send_error_message = pyqtSignal(str)
    send_status_message = pyqtSignal(str)
    send_object_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.cmd_sup = CommandSupervisor()

    def check_statuses(self):
        if self.cmd_sup.objs_dict_changed:
            self.cmd_sup.objs_dict_changed = False
            self.send_cls_obj_dict.emit(self.cmd_sup.objs_dict)
            # self.form_cls_obj_dict()
        if error_message := self.cmd_sup.error_message:
            self.send_error_message.emit(error_message)
            self.cmd_sup.error_message = ""
            print("EMIT")
        if object_check := self.cmd_sup.object_check:
            self.send_object_message.emit(object_check)
            self.cmd_sup.object_check = ""
        if common_status := self.cmd_sup.common_status:
            self.send_status_message.emit(common_status)
            self.cmd_sup.common_status = ""

    def form_cls_obj_dict(self):
        self.cmd_sup.form_cls_obj_dict()
        self.send_cls_obj_dict.emit(self.cmd_sup.objs_dict)
        # self.send_status_message.emit("Good work")

    """ Menus operations """

    def read_station_config(self, dir_name: str):
        self.cmd_sup.read_station_config(dir_name)
        self.check_statuses()

    def undo(self):
        self.cmd_sup.undo()
        self.check_statuses()

    def redo(self):
        self.cmd_sup.redo()
        self.check_statuses()

    def eval_routes(self, dir_name: str):
        # print("eval_routes dir", dir_name)
        self.cmd_sup.eval_routes(dir_name)
        self.check_statuses()

    """ Top toolbar operations """

    def create_new_object(self, cls_name: str):
        print("create", cls_name)
        self.cmd_sup.create_new_object(cls_name + "SOI")
        self.check_statuses()

    """ Left toolbar operations """

    def change_current_object(self, cls_name: str, obj_name: str):
        print("change current", cls_name, obj_name)
        self.cmd_sup.change_current_object(cls_name + "SOI", obj_name)
        self.check_statuses()

    def delete_request(self, cls_name: str, obj_name: str):
        print("delete_request", cls_name, obj_name)
        self.cmd_sup.delete_request(cls_name + "SOI", obj_name)
        del_names = [(dn[0].replace("SOI", ""), dn[1]) for dn in self.cmd_sup.deletion_names]
        self.send_delete_names.emit(del_names)
        self.check_statuses()

    def delete_confirmed(self):
        self.cmd_sup.delete_confirmed()
        self.check_statuses()

    """ Right toolbar operations """

    def change_attribute_value(self, attr_name: str, new_value: str, index: int):
        self.cmd_sup.change_attribute_value(attr_name, new_value, index)
        self.check_statuses()

    def apply_creation_new_object(self):
        self.cmd_sup.apply_creation_new_object()
        self.check_statuses()
