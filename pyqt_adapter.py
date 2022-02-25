from collections import OrderedDict

from PyQt5.QtCore import QObject, pyqtSignal

# from new_command_supervisor import CommandSupervisor
from default_ordered_dict import DefaultOrderedDict
from main_handler import MainHandler


class AdapterCorePyqtInterface(QObject):
    """ blind commander """
    send_cls_obj_dict = pyqtSignal(OrderedDict)
    send_delete_names = pyqtSignal(list)
    send_error_message = pyqtSignal(str)
    send_status_message = pyqtSignal(str)
    send_object_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.mh = MainHandler()

    def out_interface_operations(self):
        pass

        # if self.cmd_sup.objs_dict_changed:
        #     self.cmd_sup.objs_dict_changed = False
        #     self.send_cls_obj_dict.emit(self.cmd_sup.objs_dict)
        #     # self.form_cls_obj_dict()
        # if error_message := self.cmd_sup.error_message:
        #     self.send_error_message.emit(error_message)
        #     self.cmd_sup.error_message = ""
        #     print("EMIT")
        # if object_check := self.cmd_sup.object_check:
        #     self.send_object_message.emit(object_check)
        #     self.cmd_sup.object_check = ""
        # if common_status := self.cmd_sup.common_status:
        #     self.send_status_message.emit(common_status)
        #     self.cmd_sup.common_status = ""

    # def form_cls_obj_dict(self):
    #     self.cmd_sup.form_cls_obj_dict()
    #     self.send_cls_obj_dict.emit(self.cmd_sup.objs_dict)
        # self.send_status_message.emit("Good work")

    # def out_operations(self):
    #     pass

    """ Menus operations """

    def read_station_config(self, dir_name: str):
        self.mh.read_station_config(dir_name)
        self.out_interface_operations()

    def dump_station_config(self, dir_name: str):
        self.mh.dump_station_config(dir_name)
        self.out_interface_operations()

    def undo(self):
        self.mh.undo()
        self.out_interface_operations()

    def redo(self):
        self.mh.redo()
        self.out_interface_operations()

    def eval_routes(self, dir_name: str):
        self.mh.eval_routes(dir_name)
        self.out_interface_operations()

    """ Top toolbar operations """

    def create_new_object(self, cls_name: str):
        self.mh.create_new_object(cls_name + "SOI")
        self.out_interface_operations()

    """ Left toolbar operations """

    def change_current_object(self, cls_name: str, obj_name: str):
        self.mh.change_current_object(cls_name + "SOI", obj_name)
        self.out_interface_operations()

    def delete_request(self, cls_name: str, obj_name: str):
        self.mh.delete_request(cls_name + "SOI", obj_name)
        # del_names = [(dn[0].replace("SOI", ""), dn[1]) for dn in self.cmd_sup.deletion_names]
        # self.send_delete_names.emit(del_names)
        self.out_interface_operations()

    def delete_confirmed(self):
        self.mh.delete_confirmed()
        self.out_interface_operations()

    """ Right toolbar operations """

    def change_attribute_value(self, attr_name: str, new_value: str, index: int):
        self.mh.change_attribute_value(attr_name, new_value, index)
        self.out_interface_operations()

    def apply_creation_new_object(self):
        self.mh.apply_creation_new_object()
        self.out_interface_operations()

    def append_attrib_single_value(self, attr_name: str):
        self.mh.append_attrib_single_value(attr_name)
        self.out_interface_operations()

    def remove_attrib_single_value(self, attr_name: str, index: int):
        self.mh.remove_attrib_single_value(attr_name, index)
        self.out_interface_operations()
