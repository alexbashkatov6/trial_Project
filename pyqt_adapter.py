from collections import OrderedDict

from PyQt5.QtCore import QObject, pyqtSignal

# from new_command_supervisor import CommandSupervisor
from default_ordered_dict import DefaultOrderedDict
from main_handler import MainHandler


class AdapterCorePyqtInterface(QObject):
    """ blind commander """
    send_cls_obj_dict = pyqtSignal(OrderedDict)
    send_curr_obj_attrs = pyqtSignal(OrderedDict)
    send_creation_readiness = pyqtSignal(bool)

    send_delete_names = pyqtSignal(list)
    send_error_message = pyqtSignal(str)
    send_status_message = pyqtSignal(str)
    send_object_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.mh = MainHandler()

    def send_result_operations(self):
        if self.mh.changed_cls_objects_dict:
            self.send_curr_obj_attrs(self.mh.changed_cls_objects_dict)
        if self.mh.changed_current_object_attrib_dict:
            self.send_curr_obj_attrs(self.mh.current_object_attrib_dict)
        if self.mh.changed_creation_readiness:
            self.send_creation_readiness(self.mh.curr_obj_creation_readiness)

    """ Menus operations """

    def read_station_config(self, dir_name: str):
        self.mh.read_station_config(dir_name)
        self.send_result_operations()

    def dump_station_config(self, dir_name: str):
        self.mh.dump_station_config(dir_name)
        self.send_result_operations()

    def undo(self):
        self.mh.undo()
        self.send_result_operations()

    def redo(self):
        self.mh.redo()
        self.send_result_operations()

    def eval_routes(self, dir_name: str):
        self.mh.eval_routes(dir_name)
        self.send_result_operations()

    """ Top toolbar operations """

    def create_new_object(self, cls_name: str):
        self.mh.create_new_object(cls_name + "SOI")
        self.send_result_operations()

    """ Left toolbar operations """

    def change_current_object(self, cls_name: str, obj_name: str):
        self.mh.change_current_object(cls_name + "SOI", obj_name)
        self.send_result_operations()

    def delete_request(self, cls_name: str, obj_name: str):
        self.mh.delete_request(cls_name + "SOI", obj_name)
        # del_names = [(dn[0].replace("SOI", ""), dn[1]) for dn in self.cmd_sup.deletion_names]
        # self.send_delete_names.emit(del_names)
        self.send_result_operations()

    def delete_confirmed(self):
        self.mh.delete_confirmed()
        self.send_result_operations()

    """ Right toolbar operations """

    def change_attribute_value(self, attr_name: str, new_value: str, index: int):
        self.mh.change_attribute_value_logic(attr_name, new_value, index)
        self.send_result_operations()

    def apply_creation_new_object(self):
        self.mh.apply_creation_new_object()
        self.send_result_operations()

    def append_attrib_single_value(self, attr_name: str):
        self.mh.append_attrib_single_value(attr_name)
        self.send_result_operations()

    def remove_attrib_single_value(self, attr_name: str, index: int):
        self.mh.remove_attrib_single_value(attr_name, index)
        self.send_result_operations()
