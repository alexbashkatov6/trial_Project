from __future__ import annotations
from collections import OrderedDict

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from nv_config import CLASSES_SEQUENCE

""" data exchange (submit/receive) 
implemented throw dict[str, str] only  
for json-compatibility """


class ImgAttribView(QObject):
    send_attr_list = pyqtSignal(list)
    """ 
    list of attributes; format of each attribute: 
    {
    'attr_type': str, 
    'attr_name': str,
    'attr_value': str,
    'possible_values': list[str],
    'status_check': str,
    'req_type_str': str,
    'is_suggested': str
    } 
    """
    send_class_name = pyqtSignal(dict)
    """ format of data exchange {'class_name': str} """
    send_create_readiness = pyqtSignal(dict)
    """ format of data exchange {'cr_ready': str} """

    def __init__(self, manager: ImagesManager):
        super().__init__()
        self.mng = manager

    @pyqtSlot(dict)
    def set_image_class(self, d):
        """ format of data exchange {'class_name': str} """
        new_img_cls = d["class_name"]

    @pyqtSlot(dict)
    def change_attrib_value(self, d):
        """ format of data exchange {'attrib_name': str, 'attrib_value': str} """
        attrib_name = d["attrib_name"]
        attrib_value = d["attrib_value"]

    @pyqtSlot()
    def apply_changes(self):
        """ format of data exchange {} """


class ImgTreeView(QObject):
    send_tree_view = pyqtSignal(dict)
    """ format of data exchange
    {
    "classes_list":
    [
        {
        "class_name": str,
        "objects_list":
        [
            {
                "obj_name": str,
                "pick_status": str,
                "corrupt_status": str
            }
            {
                ...
            }
            ...
        ]
        }
        {
            ...
        }
        ...
    ]
    }"""
    send_object_info = pyqtSignal(dict)
    """ 
    list of attributes; format of each attribute shown above
    """

    def __init__(self, manager: ImagesManager):
        super().__init__()
        self.mng = manager

    @pyqtSlot(dict)
    def obj_hovered(self, d):
        """ format of data exchange {'hovered_obj_name': str} """
        hovered_obj_name = d["hovered_obj_name"]

    @pyqtSlot(dict)
    def obj_picked(self, d):
        """ format of data exchange {'picked_obj_name': str} """
        picked_obj_name = d["picked_obj_name"]

    @pyqtSlot(dict)
    def obj_fill(self, d):
        """ format of data exchange {'fill_obj': str} """
        fill_obj = d["fill_obj"]

    @pyqtSlot(dict)
    def obj_edit(self, d):
        """ format of data exchange {'edit_obj': str} """
        edit_obj = d["edit_obj"]

    @pyqtSlot(dict)
    def obj_delete(self, d):
        """ format of data exchange {'delete_obj': str} """
        delete_obj = d["delete_obj"]

    @pyqtSlot()
    def region_leaved(self):
        """ format of data exchange {} """


class ImgBuilder:
    def __init__(self, manager: ImagesManager):
        self.mng = manager

    def copy_obj(self):
        pass


class ImgValidator:
    def __init__(self, manager: ImagesManager):
        """
        Main idea is use built-in Python interpreter for string evaluations
        """
        self.mng = manager

    def validate_value(self):
        pass


class ImgCommandSupervisor:
    def __init__(self, manager: ImagesManager):
        """
        Undo commands for command:
        create([obj_1, obj_2, ...]) <-> delete([obj_1, obj_2, ...])
        edit(obj -> e_obj) <-> edit(e_obj -> obj)
        """
        self.mng = manager
        self.redo_commands = []
        self.undo_commands = []


class ImgDependenceGraph:
    def __init__(self, manager: ImagesManager):
        """
        Batch execution:
        virtual_builtin -> linearize -> validate_img
        """
        self.mng = manager
        self.clean_dg = None

    def virtual_builtin(self):
        pass

    def linearize(self):
        pass

    def validate_img(self):
        pass

    def read_from_file(self):
        pass

    def dump_to_file(self):
        pass


class ImagesManager:
    def __init__(self):
        self.tree_view = ImgBuilder(self)
        self.attrib_view = ImgAttribView(self)

        self.builder = ImgBuilder(self)
        self.validator = ImgValidator(self)
        self.dg = ImgDependenceGraph(self)
        self.comm_sup = ImgCommandSupervisor(self)
