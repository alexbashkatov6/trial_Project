from collections import OrderedDict

from PyQt5.QtCore import QObject, pyqtSignal

from new_command_supervisor import CommandSupervisor
from default_ordered_dict import DefaultOrderedDict


class AdapterCorePyqtInterface(QObject):
    send_cls_obj_dict = pyqtSignal(OrderedDict)
    send_delete_names = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.cmd_sup = CommandSupervisor()

    def form_cls_obj_dict(self):
        new_objs_dict = OrderedDict()
        for cls_name in self.cmd_sup.storage.soi_objects:
            cls_name_str = str(cls_name).replace("SOI", "")
            new_objs_dict[cls_name_str] = list(self.cmd_sup.storage.soi_objects[cls_name].keys())
        self.send_cls_obj_dict.emit(new_objs_dict)

    """ Menus operations """

    def read_station_config(self, dir_name: str):
        self.cmd_sup.read_station_config(dir_name)
        self.form_cls_obj_dict()
        # if self.cmd_sup.objs_dict_changed:
        #     self.cmd_sup.objs_dict_changed = False

    def undo(self):
        self.cmd_sup.undo()

    def redo(self):
        self.cmd_sup.redo()

    def eval_routes(self, dir_name: str):
        # print("eval_routes dir", dir_name)
        self.cmd_sup.eval_routes(dir_name)

    """ Top toolbar operations """

    def create_new_object(self, cls_name: str):
        print("create", cls_name)
        self.cmd_sup.create_new_object(cls_name + "SOI")

    """ Left toolbar operations """

    def change_current_object(self, cls_name: str, obj_name: str):
        print("change current", cls_name, obj_name)
        self.cmd_sup.change_current_object(cls_name + "SOI", obj_name)

    def delete_request(self, cls_name: str, obj_name: str):
        print("delete_request", cls_name, obj_name)
        self.cmd_sup.delete_request(cls_name + "SOI", obj_name)
        del_names = [(dn[0].replace("SOI", ""), dn[1]) for dn in self.cmd_sup.deletion_names]
        self.send_delete_names.emit(del_names)

    def delete_confirmed(self):
        self.cmd_sup.delete_confirmed()
        self.form_cls_obj_dict()

    """ Right toolbar operations """

    def change_attribute_value(self, attr_name: str, new_value: str, index: int):
        self.cmd_sup.change_attribute_value(attr_name, new_value, index)

    def apply_creation_new_object(self):
        self.cmd_sup.apply_creation_new_object()
