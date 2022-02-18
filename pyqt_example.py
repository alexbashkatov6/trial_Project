import sys
import traceback

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject

from main_window import MainWindow
from file_tpl_handler import FileTPLHandler
from file_id_handler import FileIdHandler
# from objects_handler import ObjectsHandler
from nv_oh import ObjectsHandler


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Oбнаружена ошибка !:", tb)


sys.excepthook = excepthook


class Director(QObject):
    def __init__(self):
        super().__init__()
        self.mw = MainWindow()
        self.file_tpl_handler = FileTPLHandler()
        self.file_id_handler = FileIdHandler()
        self.objects_handler = ObjectsHandler()

        self.mw.tpl_opened.connect(self.file_tpl_handler.handle_tpl)
        self.mw.tree_toolbar.tree_view.send_attrib_request.connect(self.objects_handler.got_object_name)
        self.mw.tree_toolbar.tree_view.send_add_new.connect(self.objects_handler.got_add_new)
        self.mw.tree_toolbar.tree_view.send_rename.connect(self.objects_handler.got_rename)
        self.mw.tree_toolbar.tree_view.send_change_class_request.connect(self.objects_handler.got_change_cls_request)
        self.mw.tree_toolbar.tree_view.send_remove_request.connect(self.objects_handler.got_remove_object_request)
        self.mw.obj_id_opened.connect(self.file_id_handler.handle_objects_id)
        self.objects_handler.send_attrib_list.connect(self.mw.attribute_toolbar.column_wgt.attrib_list_handling)

        self.file_tpl_handler.dict_formed.connect(self.objects_handler.file_tpl_got)
        self.objects_handler.send_objects_tree.connect(self.mw.tree_toolbar.tree_view.from_dict)
        self.file_id_handler.dict_formed.connect(self.objects_handler.file_obj_id_got)
        self.mw.attribute_toolbar.column_wgt.attr_edited.connect(self.objects_handler.attr_changed)
        self.mw.attribute_toolbar.column_wgt.add_element_request.connect(self.objects_handler.add_attrib_list_element)
        self.mw.attribute_toolbar.column_wgt.remove_element_request.connect(self.objects_handler.remove_attrib_list_element)

        self.mw.generate_file.connect(self.objects_handler.generate_file)

        self.mw.auto_open_tpl()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())


from collections import OrderedDict
from functools import partial
from typing import Union, Any
import os

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QToolBar, QTreeView, QVBoxLayout, QHBoxLayout, QLabel, \
    QLineEdit, QWidget, QScrollArea, QComboBox, QCompleter, QMenu, QPushButton, QSizePolicy, QAbstractScrollArea
from PyQt5.QtCore import pyqtSignal, Qt, QObject, QModelIndex
from PyQt5.Qt import QStandardItemModel, QStandardItem, QMouseEvent, QContextMenuEvent


class MainWindow(QMainWindow):
    tpl_opened = pyqtSignal(str)
    obj_id_opened = pyqtSignal(str)
    template_directory_selected = pyqtSignal(str)
    config_directory_selected = pyqtSignal(str)
    generate_file = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setGeometry(1200, 50, 600, 900)
        # self.setFixedSize(600, 300)
        self.setWindowTitle('Main window')

        # toolbars
        self.tree_toolbar = TreeToolBar()
        self.addToolBar(Qt.LeftToolBarArea, self.tree_toolbar)
        self.attribute_toolbar = AttributeToolBar()
        self.addToolBar(Qt.RightToolBarArea, self.attribute_toolbar)

        # menus
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu('&File')
        open_tpl_action = file_menu.addAction("&Open TPL")
        open_tpl_action.triggered.connect(self.open_tpl)
        open_obj_id_action = file_menu.addAction("&Open Obj Id")
        open_obj_id_action.triggered.connect(self.open_obj_id)
        save_template_action = file_menu.addAction("&Save Template")
        save_template_action.triggered.connect(self.save_template)
        save_config_action = file_menu.addAction("&Save config")
        save_config_action.triggered.connect(self.save_config)

        gen_menu = menu_bar.addMenu('&Generators')
        gen_point_action = gen_menu.addAction("&TObjectsPoint")
        gen_point_action.triggered.connect(self.gen_point)

        self.show()

    def open_tpl(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', './input/', 'xml Files (*.xml)')
        if not file_name:
            return
        self.tpl_opened.emit(file_name)

    def open_obj_id(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', './input/', 'xml Files (*.xml)')
        if not file_name:
            return
        self.obj_id_opened.emit(file_name)

    def auto_open_tpl(self):
        file_name = os.path.join(os.getcwd(), "input", "TPL.xml")
        self.tpl_opened.emit(file_name)

    def save_template(self):
        dir_name = QFileDialog.getExistingDirectory(self, 'Save', './output/')
        if not dir_name:
            return
        self.template_directory_selected.emit(dir_name)

    def save_config(self):
        dir_name = QFileDialog.getExistingDirectory(self, 'Save', './output/')
        if not dir_name:
            return
        self.config_directory_selected.emit(dir_name)

    def gen_point(self):
        self.generate_file.emit("TObjectsPoint")


class TreeToolBarWidget(QTreeView):
    send_add_new = pyqtSignal(str)
    send_rename = pyqtSignal(str, str)
    send_attrib_request = pyqtSignal(str)
    send_remove_request = pyqtSignal(str)
    send_change_class_request = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.tree_model = QStandardItemModel()
        self.tree_model.itemChanged.connect(self.item_changed)
        self.root_node = self.tree_model.invisibleRootItem()
        self.setModel(self.tree_model)
        self.setHeaderHidden(True)
        self.class_names: set[str] = set()
        self.simple_shunting_names: set[str] = set()
        self.adj_point_shunting_names: set[str] = set()
        self.obj_names: set[str] = set()
        self.index_to_str: dict[QModelIndex, str] = {}
        self.expanded_indexes: set[QModelIndex] = set()
        self.expanded.connect(self.add_expanded_index)
        self.collapsed.connect(self.remove_expanded_index)

    def add_expanded_index(self, idx: QModelIndex):
        self.expanded_indexes.add(idx)

    def remove_expanded_index(self, idx: QModelIndex):
        self.expanded_indexes.remove(idx)

    def item_changed(self, item: QStandardItem):
        self.send_rename.emit(self.index_to_str[item.index()], item.text())
        # print("item_index", item.index(self.index_to_str[item.index()], item.text()))
        # print("item_old", self.index_to_str[item.index()])
        # print("item_new", item.text())

    def from_dict(self, d: OrderedDict[str, list[str]]):
        self.class_names.clear()
        self.obj_names.clear()
        self.simple_shunting_names.clear()
        self.adj_point_shunting_names.clear()

        self.root_node.removeRows(0, self.root_node.rowCount())
        self.root_node.emitDataChanged()
        for class_name in d:
            self.class_names.add(class_name)
            item_class = QStandardItem(class_name)
            item_class.setEditable(False)
            item_class.setSelectable(False)
            self.root_node.appendRow(item_class)
            for obj_name in d[class_name]:
                if class_name == "PpoShuntingSignal":
                    self.simple_shunting_names.add(obj_name)
                if class_name == "PpoShuntingSignalWithTrackAnD":
                    self.adj_point_shunting_names.add(obj_name)
                self.obj_names.add(obj_name)
                item_obj = QStandardItem(obj_name)
                item_class.appendRow(item_obj)
                self.index_to_str[item_obj.index()] = obj_name
        for idx in self.expanded_indexes:
            self.expand(idx)

    # def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None:
    #     data = self.indexAt(a0.localPos().toPoint()).data()
    #     if data:
    #         self.send_attrib_request.emit(data)

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            data = self.indexAt(a0.localPos().toPoint()).data()
            if not (data is None):
                self.send_attrib_request.emit(data)

    def contextMenuEvent(self, a0: QContextMenuEvent):
        data = self.indexAt(a0.pos()).data()
        if data and (not data.isspace()) and ("OBJECTS" not in data):
            contextMenu = QMenu(self)
            if data in self.class_names:
                contextMenu.addAction("Add new object").triggered.\
                    connect(partial(self.send_add_new_, val=self.indexAt(a0.pos()).data()))

            elif data in self.obj_names:
                contextMenu.addAction("Get attributes").triggered.\
                    connect(partial(self.send_attrib_request_, val=self.indexAt(a0.pos()).data()))
                contextMenu.addAction("Remove").triggered.\
                    connect(partial(self.send_remove_request_, val=self.indexAt(a0.pos()).data()))
                if data in self.simple_shunting_names:
                    contextMenu.addAction("Move to adj point shunting").triggered.\
                        connect(partial(self.send_change_class_request_,
                                        val=self.indexAt(a0.pos()).data(),
                                        cls_to="PpoShuntingSignalWithTrackAnD"))
                if data in self.adj_point_shunting_names:
                    contextMenu.addAction("Move to simple shunting").triggered.\
                        connect(partial(self.send_change_class_request_,
                                        val=self.indexAt(a0.pos()).data(),
                                        cls_to="PpoShuntingSignal"))

            contextMenu.exec_(self.mapToGlobal(a0.pos()))

    def send_add_new_(self, val: str):
        self.send_add_new.emit(val)

    def send_attrib_request_(self, val: str):
        self.send_attrib_request.emit(val)

    def send_remove_request_(self, val: str):
        self.send_remove_request.emit(val)

    def send_change_class_request_(self, val: str, cls_to: str):
        self.send_change_class_request.emit(val, cls_to)


class TreeToolBar(QToolBar):
    def __init__(self):
        super().__init__()
        self.setMovable(False)
        self.setMinimumWidth(300)
        self.tree_view = TreeToolBarWidget()
        self.addWidget(self.tree_view)


class AttributeWidget(QWidget):
    attr_edited = pyqtSignal(list, str)
    add_element_request = pyqtSignal(list)
    remove_element_request = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        self.external_layout = QVBoxLayout()
        self.internal_widget = QWidget()
        # self.internal_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.scroll_widget = QScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        self.external_layout.addWidget(self.scroll_widget)
        self.scroll_widget.setWidget(self.internal_widget)
        self.column_layout = QVBoxLayout()
        self.column_layout.setSpacing(0)
        self.column_layout.setContentsMargins(0, 0, 0, 0)
        self.internal_widget.setLayout(self.column_layout)
        self.setLayout(self.external_layout)
        self.space_indexes = []
        self.last_clicked_index = 0
        self.widget_indexes = {}
        self.last_clicked_point = (0, 0)
        self.old_slider_position = 0

    def edit_finished(self, address):
        line_edit: QLineEdit = self.sender()
        self.old_slider_position = self.scroll_widget.verticalScrollBar().sliderPosition()
        if line_edit.completer():
            completer = line_edit.completer()
            completer.popup().setVisible(False)
        self.attr_edited.emit(address, line_edit.text())

    def add_element(self, address):
        self.old_slider_position = self.scroll_widget.verticalScrollBar().sliderPosition()
        self.add_element_request.emit(address)

    def remove_element(self, address):
        self.old_slider_position = self.scroll_widget.verticalScrollBar().sliderPosition()
        self.remove_element_request.emit(address)

    def reset_color_editing(self, s: str):
        line_edit: QLineEdit = self.sender()
        line_edit.setStyleSheet("background-color: white")

    def recursive_remove_widget(self, start_widget: QWidget):
        for child in start_widget.children():
            if isinstance(child, QWidget):
                self.recursive_remove_widget(child)
            if not (start_widget is self.internal_widget):
                start_widget.setParent(None)

    def attrib_list_handling(self, info_list: list):
        for idx in reversed(self.space_indexes):
            self.column_layout.removeItem(self.column_layout.itemAt(idx))
        self.space_indexes = []
        self.recursive_remove_widget(self.internal_widget)
        self.list_expansion(info_list)

    def list_expansion(self, info_list: list):
        self.internal_widget.setMinimumHeight(len(info_list)*28)
        for row in info_list:
            if row[0][0] == "Spacing":
                self.space_indexes.append(self.column_layout.count())
                self.column_layout.addSpacing(int(row[0][1]))
                continue
            else:
                horizontal_wgt = QWidget(self)
                horizontal_layout = QHBoxLayout()
                horizontal_layout.setContentsMargins(2, 2, 2, 2)
                horizontal_wgt.setLayout(horizontal_layout)
                for elem in row:
                    elem: tuple[str, Any]
                    if elem[0] == "Label":
                        od: OrderedDict[str, Any] = elem[1]
                        label = QLabel(od["current_value"])
                        label.setMinimumHeight(20)
                        label.setContentsMargins(2, 2, 2, 2)
                        if od["is_centered"]:
                            horizontal_layout.addWidget(label, alignment=Qt.AlignCenter)
                        else:
                            horizontal_layout.addWidget(label)
                    if elem[0] == "Button":
                        od: OrderedDict[str, Any] = elem[1]
                        if od["is_add_button"]:
                            button = QPushButton("Add")
                            button.setMinimumHeight(20)
                            button.setContentsMargins(2, 2, 2, 2)
                            button.clicked.connect(partial(self.add_element, address=od["address"]))
                        else:
                            button = QPushButton("Remove")
                            button.setMinimumHeight(20)
                            button.setContentsMargins(2, 2, 2, 2)
                            button.clicked.connect(partial(self.remove_element, address=od["address"]))
                        horizontal_layout.addWidget(button)
                    if elem[0] == "LineEdit":
                        od: OrderedDict[str, Any] = elem[1]
                        line_edit = QLineEdit(od["current_value"])
                        line_edit.setParent(self.internal_widget)
                        line_edit.setMinimumHeight(20)
                        line_edit.setContentsMargins(2, 2, 2, 2)
                        possible_values = od["possible_values"]
                        if possible_values:
                            completer = QCompleter(possible_values, self)
                            line_edit.setCompleter(completer)
                        line_edit.returnPressed.connect(partial(self.edit_finished, address=od["address"]))
                        line_edit.textEdited.connect(self.reset_color_editing)
                        check_status = od["check_status"]
                        if check_status:
                            line_edit.setStyleSheet("background-color: #f00")
                        elif od["current_value"]:
                            line_edit.setStyleSheet("background-color: #0f0")
                        else:
                            line_edit.setStyleSheet("background-color: white")
                        horizontal_layout.addWidget(line_edit)
                self.column_layout.addWidget(horizontal_wgt)
        self.space_indexes.append(self.column_layout.count())
        self.column_layout.addStretch(1)
        self.scroll_widget.verticalScrollBar().setSliderPosition(self.old_slider_position)


class AttributeToolBar(QToolBar):
    def __init__(self):
        super().__init__()
        self.setMovable(False)
        self.setMinimumWidth(300)
        self.column_wgt = AttributeWidget()
        self.addWidget(self.column_wgt)

        # label = QLabel("LALA")
        # label.setFixedSize(1000, 1000)
        # label.setStyleSheet("font-size: 320px")
        # self.scroll_area = QScrollArea()
        # self.scroll_area.setWidget(label)
        # self.scroll_area.ensureWidgetVisible(label)
        # self.addWidget(self.scroll_area)
from __future__ import annotations

import os.path
from collections import OrderedDict
from typing import Type, Iterable, Optional, Any, Callable, Union
import json
from functools import partial
from copy import copy

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QObject

tpl_to_obj_id: OrderedDict[str, str] = OrderedDict()
tpl_to_obj_id['PpoPoint'] = "Str"
tpl_to_obj_id['PpoTrainSignal'] = "SvP"
tpl_to_obj_id['PpoShuntingSignal'] = "SvM"
tpl_to_obj_id['PpoPointSection'] = "SPU"
tpl_to_obj_id['PpoTrackSection'] = "SPU"
tpl_to_obj_id['PpoTrackAnD'] = "Put"
tpl_to_obj_id['PpoAutomaticBlockingSystem'] = "AdjAB"
tpl_to_obj_id['PpoSemiAutomaticBlockingSystem'] = "AdjPAB"
tpl_to_obj_id['PpoLineEnd'] = "Tpk"
tpl_to_obj_id['PpoControlAreaBorder'] = "GRU"


class TagRepeatingError(Exception):
    pass


class NotPossibleValueError(Exception):
    pass


# --------------------------  DESCRIPTORS  ------------------------


class DefaultDescriptor:

    def __init__(self, default_value: Any = None, is_required: bool = True, is_list: bool = False, min_count: int = 1,
                 no_repeating_values: bool = True):
        self.name = None
        self.default_value = default_value
        self.is_required = is_required
        self.is_list = is_list
        self.min_count = min_count
        self.no_repeating_values = no_repeating_values

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if not instance:
            return self
        attr_val = "_{}".format(self.name)
        if not hasattr(instance, attr_val):
            if self.is_list:
                setattr(instance, "_{}".format(self.name), [""] * self.min_count)
                setattr(instance, "_str_{}".format(self.name), [""] * self.min_count)
                setattr(instance, "_check_status_{}".format(self.name), [""] * self.min_count)
            elif self.default_value:
                setattr(instance, "_{}".format(self.name), self.default_value)
                setattr(instance, "_str_{}".format(self.name), self.default_value)
                setattr(instance, "_check_status_{}".format(self.name), "")
            else:
                setattr(instance, "_{}".format(self.name), "")
                setattr(instance, "_str_{}".format(self.name), "")
                setattr(instance, "_check_status_{}".format(self.name), "")
        return getattr(instance, "_str_{}".format(self.name))

    def __set__(self, instance, input_value):
        setattr(instance, "_str_{}".format(self.name), input_value)
        setattr(instance, "_{}".format(self.name), input_value)


class ObjectListDescriptor(DefaultDescriptor):

    def __init__(self, obj_type: Type, is_required: bool = True, min_count: int = 1, no_repeating_values: bool = True):
        super().__init__(None, is_required, True, min_count, no_repeating_values)
        self.obj_type = obj_type

    def __get__(self, instance, owner):
        if not instance:
            return self
        attr_val = "_{}".format(self.name)
        if not hasattr(instance, attr_val):
            objs_list = []
            for i in range(self.min_count):
                obj = self.obj_type()
                objs_list.append(obj)
            setattr(instance, attr_val, objs_list)
        return getattr(instance, attr_val)

    def __set__(self, instance, input_value: list):
        setattr(instance, "_{}".format(self.name), input_value)


class StrBoundedValuesDescriptor(DefaultDescriptor):

    def __init__(self, default_value: Any = None, is_required: bool = True, is_list: bool = False, min_count: int = 1,
                 no_repeating_values: bool = True):
        super().__init__(default_value, is_required, is_list, min_count, no_repeating_values)
        self._possible_values = []

    def __set__(self, instance, input_value: Union[str, list[str]]):
        setattr(instance, "_str_{}".format(self.name), input_value)
        if not self.possible_values:
            setattr(instance, "_{}".format(self.name), input_value)
            if self.is_list:
                init_check_value = [""] * len(input_value)
            else:
                init_check_value = ""
            setattr(instance, "_check_status_{}".format(self.name), init_check_value)
        else:
            if not self.is_list:
                if (self.default_value and (input_value == self.default_value)) or (
                        input_value in self.possible_values):
                    setattr(instance, "_{}".format(self.name), input_value)
                    setattr(instance, "_check_status_{}".format(self.name), "")
                else:
                    setattr(instance, "_check_status_{}".format(self.name),
                            "Value {} not in list of possible values: {}".format(input_value, self.possible_values))
            else:
                old_destination_list = getattr(instance, "_{}".format(self.name))
                destination_list = []
                check_list = []
                for i, value in enumerate(input_value):
                    destination_list.append("")
                    check_list.append("")
                    if (self.default_value and (value == self.default_value)) or (value in self.possible_values):
                        destination_list[-1] = value
                        check_list[-1] = ""
                    else:
                        check_list[-1] = "Value {} not in list of possible values: {}".format(value,
                                                                                              self.possible_values)
                        if i < len(old_destination_list):
                            destination_list[i] = old_destination_list[i]
                setattr(instance, "_{}".format(self.name), destination_list)
                setattr(instance, "_check_status_{}".format(self.name), check_list)

    @property
    def possible_values(self) -> list[str]:
        result = list(self._possible_values)
        if self.default_value:
            result.append(self.default_value)
        return result

    @possible_values.setter
    def possible_values(self, values: Iterable[str]):
        self._possible_values = values


class ClassNameDescriptor:
    def __get__(self, instance, owner):
        return owner.__name__

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class TagDescriptor:
    def __init__(self):
        self.tags = set()

    def __get__(self, instance, owner):
        if not instance:
            return self
        return getattr(instance, "_tag")

    def __set__(self, instance, value: str):
        instance._tag = value
        self.tags.add(instance._tag)


class AllAttributesOdDescriptor:
    def __init__(self):
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if not instance:
            return [key for key in owner.__dict__.keys() if not key.startswith("__")]

        result = OrderedDict()
        for attr_name in getattr(owner, self.name):
            result[attr_name] = getattr(instance, attr_name)
        return result


class DataDescriptor:

    def __get__(self, instance, owner):
        if not instance:
            return [key for key in owner.__dict__.keys() if not key.startswith("__")]

        data_odict = OrderedDict()
        for attr_name in owner.data:
            if attr_name == "id_":
                data_odict["id"] = getattr(instance, attr_name)
            else:
                descr = getattr(owner, attr_name)
                if isinstance(descr, ObjectListDescriptor):
                    obj_list = getattr(instance, attr_name)
                    result = []
                    for obj in obj_list:
                        all_attrs = obj.all_attributes
                        result.append(all_attrs)
                    data_odict[attr_name] = result
                else:
                    data_odict[attr_name] = getattr(instance, attr_name)
        return data_odict

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class ToJsonDescriptor:

    def __get__(self, instance, owner):
        if not instance:
            return self
        instance: PpoObject

        odict = OrderedDict()
        odict["class"] = instance.class_
        odict["tag"] = instance.tag
        odict["data"] = instance.data

        return odict

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class EqualTagDescriptor(DefaultDescriptor):

    def __get__(self, instance, owner):
        if not instance:
            return self
        attr_val = "_{}".format(self.name)
        if not hasattr(instance, attr_val):
            setattr(instance, "_{}".format(self.name), instance.tag)
            setattr(instance, "_str_{}".format(self.name), instance.tag)
            setattr(instance, "_check_status_{}".format(self.name), "")
        return getattr(instance, "_str_{}".format(self.name))


class IdDescriptor(EqualTagDescriptor):
    pass


class IndentDescriptor(EqualTagDescriptor):
    pass


class IdControlAreaDescriptor(StrBoundedValuesDescriptor):
    pass


class IObjTagSimpleDescriptor(EqualTagDescriptor):
    pass


class RoutePointersDescriptor(StrBoundedValuesDescriptor):
    pass


class UkspsDescriptor(StrBoundedValuesDescriptor):
    pass


class IntDescriptor(DefaultDescriptor):

    def __set__(self, instance, value: str):
        setattr(instance, "_str_{}".format(self.name), value)
        if not value.isdigit():
            setattr(instance, "_check_status_{}".format(self.name), "Input value {} is not a number".format(value))
        else:
            setattr(instance, "_{}".format(self.name), value)
            setattr(instance, "_check_status_{}".format(self.name), "")


class LengthDescriptor(IntDescriptor):
    pass


class TrackUnitDescriptor(StrBoundedValuesDescriptor):
    pass


class PointsMonitoringDescriptor(DefaultDescriptor):

    def __get__(self, instance, owner):
        if not instance:
            return self
        attr_val = "_{}".format(self.name)
        if not hasattr(instance, attr_val):
            setattr(instance, "_{}".format(self.name), "STRELKI")
            setattr(instance, "_str_{}".format(self.name), "STRELKI")
            setattr(instance, "_check_status_{}".format(self.name), "")
        return getattr(instance, "_str_{}".format(self.name))


class SectionDescriptor(StrBoundedValuesDescriptor):
    pass


class RailFittersWarningAreaDescriptor(EqualTagDescriptor):
    pass


class AutoReturnDescriptor(StrBoundedValuesDescriptor):
    pass


class PointDescriptor(StrBoundedValuesDescriptor):
    pass


class LockingDescriptor(StrBoundedValuesDescriptor):
    pass


class PlusMinusDescriptor(StrBoundedValuesDescriptor):
    pass


class IsInvitationSignalOpeningBeforeDescriptor(StrBoundedValuesDescriptor):
    pass


class SingleTrackDescriptor(StrBoundedValuesDescriptor):
    pass


class RailCrossingDescriptor(StrBoundedValuesDescriptor):
    pass


class AddrKiDescriptor(StrBoundedValuesDescriptor):
    def __init__(self, default_value: Any = None, is_required: bool = True, is_list: bool = False, min_count: int = 1,
                 no_repeating_values: bool = True):
        default_value = "USO:::"
        super().__init__(default_value, is_required, is_list, min_count, no_repeating_values)
        self.possible_values = ["USO", "CPU", "PPO", "Fixed_1", "Fixed_0"]

    def __set__(self, instance, value: str):
        super().__set__(instance, value)
        value = value.strip()
        if value.startswith("USO") or value.startswith("CPU") or value.startswith("PPO"):
            between_column = value.split(":")
            if len(between_column) == 2:
                if between_column[0] != "PPO":
                    setattr(instance, "_check_status_{}".format(self.name),
                            "Address not valid begin: {}".format(value))
                    return
                if between_column[1] not in ["MAX_UINT", "0"]:
                    setattr(instance, "_check_status_{}".format(self.name),
                            "Address not valid end: {}".format(value))
                    return
                setattr(instance, "_check_status_{}".format(self.name), "")
                setattr(instance, "_{}".format(self.name), value)
                return
            if len(between_column) < 4:
                setattr(instance, "_check_status_{}".format(self.name),
                        "Count of colon <3 in value: {}".format(value))
                return
            if between_column[0] not in ["USO", "CPU", "PPO"]:
                setattr(instance, "_check_status_{}".format(self.name),
                        "Address not valid begin: {}".format(value))
                return
            for addr_int in between_column[1:]:
                if not addr_int.isdigit():
                    setattr(instance, "_check_status_{}".format(self.name),
                            "Address not valid because not digits: {}".format(value))
                    return
            setattr(instance, "_check_status_{}".format(self.name), "")
            setattr(instance, "_{}".format(self.name), value)


class AddrUiDescriptor(StrBoundedValuesDescriptor):
    def __init__(self, default_value: Any = None, is_required: bool = True, is_list: bool = False, min_count: int = 1,
                 no_repeating_values: bool = True):
        default_value = "USO:::"
        super().__init__(default_value, is_required, is_list, min_count, no_repeating_values)
        self.possible_values = ["USO", "CPU", "PPO", "addrKI_1U", "NoAddr"]

    def __set__(self, instance, value: str):
        super().__set__(instance, value)
        value = value.strip()
        if value.startswith("USO") or value.startswith("CPU") or value.startswith("PPO"):
            between_column = value.split(":")
            if len(between_column) < 4:
                setattr(instance, "_check_status_{}".format(self.name),
                        "Count of colon <3 in value: {}".format(value))
                return
            if between_column[0] not in ["USO", "CPU", "PPO"]:
                setattr(instance, "_check_status_{}".format(self.name),
                        "Address not valid begin: {}".format(value))
                return
            for addr_int in between_column[1:]:
                if not addr_int.isdigit():
                    setattr(instance, "_check_status_{}".format(self.name),
                            "Address not valid because not digits: {}".format(value))
                    return
            setattr(instance, "_check_status_{}".format(self.name), "")
            setattr(instance, "_{}".format(self.name), value)


class InterstationDirectiveDescriptor(StrBoundedValuesDescriptor):
    def __init__(self, default_value: Any = None, is_required: bool = True, is_list: bool = False, min_count: int = 1,
                 no_repeating_values: bool = True):
        super().__init__(default_value, is_required, is_list, min_count, no_repeating_values)
        self.possible_values = ["NoAddr"]

    def __get__(self, instance, owner):
        if not instance:
            return self
        self.default_value = "{}_{}".format(self.name.split("_")[1], instance.tag.replace("_Ri", ""))
        return super().__get__(instance, owner)


class CrossroadDescriptor(StrBoundedValuesDescriptor):
    pass


class IObjTagTrackCrossroadDescriptor(StrBoundedValuesDescriptor):
    pass


class ModeLightSignalDescriptor(DefaultDescriptor):

    def __get__(self, instance, owner):
        if not instance:
            return self
        attr_val = "_{}".format(self.name)
        if not hasattr(instance, attr_val):
            setattr(instance, "_{}".format(self.name), "DN_DSN")
            setattr(instance, "_str_{}".format(self.name), "DN_DSN")
            setattr(instance, "_check_status_{}".format(self.name), "")
        return getattr(instance, "_str_{}".format(self.name))


class AddrCiDescriptor(AddrKiDescriptor):

    def __set__(self, instance, value: str):
        if value.isdigit():
            setattr(instance, "_check_status_{}".format(self.name), "")
            setattr(instance, "_{}".format(self.name), value)
        super().__set__(instance, value)


class TypeLightSignalDescriptor(IntDescriptor):
    pass


class EnterSignalDescriptor(StrBoundedValuesDescriptor):
    pass


class IObjTagTrackUnitDescriptor(StrBoundedValuesDescriptor):
    pass


class EncodingPointDescriptor(StrBoundedValuesDescriptor):
    pass


class DirectionPointAndTrackDescriptor(StrBoundedValuesDescriptor):
    pass


class OppositeTrackAnDwithPointDescriptor(StrBoundedValuesDescriptor):
    pass


class AdjEnterSigDescriptor(StrBoundedValuesDescriptor):
    pass


# --------------------------  OBJECT CLASSES  ------------------------


class PpoObject:
    class_ = ClassNameDescriptor()
    tag = TagDescriptor()
    data = DataDescriptor()
    to_json = ToJsonDescriptor()
    all_attributes = AllAttributesOdDescriptor()


class PpoRoutePointer(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    routePointer = RoutePointersDescriptor()


class PpoRoutePointerRi(PpoObject):
    onRoutePointer = AddrUiDescriptor()
    outputAddrs = AddrUiDescriptor()


class PpoTrainSignal(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    iObjTag = IObjTagSimpleDescriptor()
    routePointer = RoutePointersDescriptor()
    groupRoutePointers = RoutePointersDescriptor(is_list=True)
    uksps = UkspsDescriptor()


class PpoShuntingSignal(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    iObjTag = IObjTagSimpleDescriptor()


class PpoShuntingSignalWithTrackAnD(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    iObjTag = IObjTagSimpleDescriptor()


class PpoLightSignalCi(PpoObject):
    mode = ModeLightSignalDescriptor()
    addrKa = AddrCiDescriptor()
    addrKi = AddrCiDescriptor()
    addrUi = AddrCiDescriptor()
    type_ = TypeLightSignalDescriptor()


class PpoAnDtrack(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    length = LengthDescriptor(default_value="5")
    trackUnit = TrackUnitDescriptor()


class PpoTrackAnDwithPoint(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    length = LengthDescriptor(default_value="5")
    trackUnit = TrackUnitDescriptor()
    directionPointAnDTrack = DirectionPointAndTrackDescriptor()
    oppositeTrackAnDwithPoint = OppositeTrackAnDwithPointDescriptor()


class PpoLineEnd(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    length = LengthDescriptor(default_value="5")
    trackUnit = TrackUnitDescriptor(default_value="nullptr")


class PpoPointSection(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    length = LengthDescriptor(default_value="5")
    trackUnit = TrackUnitDescriptor()


class PpoTrackSection(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    length = LengthDescriptor(default_value="5")
    trackUnit = TrackUnitDescriptor()


class AdditionalSwitch(PpoObject):
    point = PointDescriptor()
    selfPosition = PlusMinusDescriptor()
    dependencePosition = PlusMinusDescriptor()


class SectionAndIgnoreCondition(PpoObject):
    section = SectionDescriptor()
    point = PointDescriptor()
    position = PlusMinusDescriptor()


class NotificationPoint(PpoObject):
    point = AddrKiDescriptor()
    delay = AddrKiDescriptor()


class PpoPoint(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    iObjTag = IObjTagSimpleDescriptor()
    pointsMonitoring = PointsMonitoringDescriptor()
    section = SectionDescriptor()
    railFittersWarningArea = RailFittersWarningAreaDescriptor()
    autoReturn = AutoReturnDescriptor()
    guardPlusPlus = PointDescriptor(is_list=True)
    guardPlusMinus = PointDescriptor(is_list=True)
    guardMinusPlus = PointDescriptor(is_list=True)
    guardMinusMinus = PointDescriptor(is_list=True)
    lockingPlus = LockingDescriptor(is_list=True)
    lockingMinus = LockingDescriptor(is_list=True)
    additionalSwitch = ObjectListDescriptor(obj_type=AdditionalSwitch)
    pairPoint = PointDescriptor()
    oversizedPlus = ObjectListDescriptor(obj_type=SectionAndIgnoreCondition)
    oversizedMinus = ObjectListDescriptor(obj_type=SectionAndIgnoreCondition)
    additionalGuardLock = ObjectListDescriptor(obj_type=SectionAndIgnoreCondition)


class PpoControlAreaBorder(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()


class PpoSemiAutomaticBlockingSystem(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    iObjTag = IObjTagSimpleDescriptor()
    isInvitationSignalOpeningBefore = IsInvitationSignalOpeningBeforeDescriptor()


class PpoSemiAutomaticBlockingSystemRi(PpoObject):
    addrKI_SNP = AddrKiDescriptor()
    addrKI_S1U = AddrKiDescriptor()
    addrKI_1U = AddrKiDescriptor()
    addrKI_FP = AddrKiDescriptor()
    addrKI_POS = AddrKiDescriptor()
    addrKI_PS = AddrKiDescriptor()
    addrKI_OP = AddrKiDescriptor()
    addrKI_DSO = AddrKiDescriptor()
    addrKI_KZH = AddrKiDescriptor()

    addrUI_KS = AddrUiDescriptor()

    output_DSO = InterstationDirectiveDescriptor()
    output_OSO = InterstationDirectiveDescriptor()
    output_FDP = InterstationDirectiveDescriptor()
    output_IFP = InterstationDirectiveDescriptor()

    notificationPoints = ObjectListDescriptor(obj_type=NotificationPoint)


class PpoAutomaticBlockingSystem(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    iObjTag = IObjTagSimpleDescriptor()
    isInvitationSignalOpeningBefore = IsInvitationSignalOpeningBeforeDescriptor()
    singleTrack = SingleTrackDescriptor()


class PpoAutomaticBlockingSystemRi(PpoObject):
    addrKI_SNP = AddrKiDescriptor()
    addrKI_SN = AddrKiDescriptor()
    addrKI_S1U = AddrKiDescriptor()
    addrKI_S1P = AddrKiDescriptor()
    addrKI_1U = AddrKiDescriptor()
    addrKI_1P = AddrKiDescriptor()
    addrKI_2U = AddrKiDescriptor()
    addrKI_3U = AddrKiDescriptor()
    addrKI_ZU = AddrKiDescriptor()
    addrKI_KP = AddrKiDescriptor()
    addrKI_KZH = AddrKiDescriptor()
    addrKI_UUB = AddrKiDescriptor()
    addrKI_PB = AddrKiDescriptor()
    addrKI_KV = AddrKiDescriptor()
    addrKI_A = AddrKiDescriptor()

    addrUI_KS = AddrUiDescriptor()
    addrUI_I = AddrUiDescriptor()
    addrUI_KZH = AddrUiDescriptor()
    addrUI_VIP1 = AddrUiDescriptor()
    addrUI_VIP2 = AddrUiDescriptor()
    addrUI_VIP3 = AddrUiDescriptor()
    addrUI_OKV = AddrUiDescriptor()
    addrUI_KM = AddrUiDescriptor()

    output_SNK = InterstationDirectiveDescriptor()
    output_DS = InterstationDirectiveDescriptor()
    output_OV = InterstationDirectiveDescriptor()
    output_PV = InterstationDirectiveDescriptor()
    output_RUU = InterstationDirectiveDescriptor()
    output_R = InterstationDirectiveDescriptor()

    adjEnterSig = AdjEnterSigDescriptor()

    notificationPoints = ObjectListDescriptor(obj_type=NotificationPoint)


class PpoTrackCrossroad(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    iObjTag = IObjTagTrackCrossroadDescriptor()
    railCrossing = RailCrossingDescriptor()


class PpoTrainNotificationRi(PpoObject):
    NPI = AddrUiDescriptor()
    CHPI = AddrUiDescriptor()


class PpoRailCrossingRi(PpoObject):
    NCHPI = AddrKiDescriptor()
    KP_O = AddrKiDescriptor()
    KP_A = AddrKiDescriptor()
    ZG = AddrKiDescriptor()
    KZP = AddrKiDescriptor()


class PpoRailCrossing(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    iObjTag = IObjTagSimpleDescriptor()
    crossroad = CrossroadDescriptor(is_list=True)


class PpoControlDeviceDerailmentStock(PpoObject):
    id_ = IdDescriptor()
    indent = IndentDescriptor()
    idControlArea = IdControlAreaDescriptor()
    iObjTag = IObjTagSimpleDescriptor()


class PpoControlDeviceDerailmentStockCi(PpoObject):
    addrKI_1KSO = AddrCiDescriptor()
    addrKI_1KSR = AddrCiDescriptor()
    addrKI_2KSO = AddrCiDescriptor()
    addrKI_2KSR = AddrCiDescriptor()

    addrKI_KSV = AddrKiDescriptor()
    addrKI_SNP = AddrKiDescriptor()
    addrKI_1UP = AddrKiDescriptor()
    addrKI_2UP = AddrKiDescriptor()
    addrKI_1UU = AddrKiDescriptor()
    addrKI_2UU = AddrKiDescriptor()

    addrUI_1KSD = AddrUiDescriptor()
    addrUI_2KSB = AddrUiDescriptor()
    addrUI_KSVA = AddrUiDescriptor()

    enterSignal = EnterSignalDescriptor()


class PpoTrackUnit(PpoObject):
    iObjsTag = IObjTagTrackUnitDescriptor()
    evenTag = EncodingPointDescriptor()
    oddTag = EncodingPointDescriptor()


class PpoTrackReceiverRi(PpoObject):
    addrKI_P = AddrKiDescriptor()


class PpoLightSignalRi(PpoObject):
    addrKI_KO = AddrKiDescriptor()
    addrKI_KPS = AddrKiDescriptor()
    addrKI_RU = AddrKiDescriptor()
    addrKI_GM = AddrKiDescriptor()
    addrKI_KMGS = AddrKiDescriptor()
    addrKI_ZHZS = AddrKiDescriptor()
    addrKI_ZS = AddrKiDescriptor()


# --------------------------  HANDLER  ------------------------


def check_not_repeating_names(odict):
    names = []
    for cls_name in odict:
        for obj_name in odict[cls_name]:
            if obj_name in names:
                raise TagRepeatingError("Tag {} repeats".format(obj_name))
            names.append(obj_name)


class ObjectsHandler(QObject):
    send_objects_tree = pyqtSignal(OrderedDict)
    send_attrib_list = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.bool_tpl_got = False
        self.bool_obj_id_got = False
        self.tpl_dict: OrderedDict[str, list[str]] = OrderedDict()  # input structure from tpl
        self.obj_id_dict: OrderedDict[str, list[str]] = OrderedDict()

        self.objects_tree: OrderedDict[str, OrderedDict[str, PpoObject]] = OrderedDict()  # output structure

        self.current_object: Optional[PpoObject] = None

    @property
    def obj_name_to_cls_name_dict(self):
        result: OrderedDict[str, str] = OrderedDict()
        for cls_name in self.objects_tree:
            result.update(OrderedDict.fromkeys(self.objects_tree[cls_name], cls_name))
        return result

    @property
    def str_objects_tree(self) -> OrderedDict[str, list[str]]:
        result: OrderedDict[str, list[str]] = OrderedDict()
        for cls_name in self.objects_tree:
            result[cls_name] = list(self.objects_tree[cls_name].keys())
        return result

    @property
    def name_to_obj_dict(self) -> OrderedDict[str, PpoObject]:
        result: OrderedDict[str, PpoObject] = OrderedDict()
        for cls_name in self.objects_tree:
            result.update(self.objects_tree[cls_name])
        return result

    def init_object(self, cls_name, obj_name):
        if cls_name == "PpoTrackAnD":
            cls_ = PpoAnDtrack
            obj = cls_()
            obj.tag = obj_name
            if cls_name not in self.objects_tree:
                self.objects_tree[cls_name] = OrderedDict()
            self.objects_tree[cls_name][obj_name] = obj

        elif cls_name in ["PpoTrainSignal", "PpoShuntingSignal"]:
            tpo_cls_ = eval(cls_name)
            tpo_obj = tpo_cls_()
            tpo_obj.tag = obj_name
            if cls_name not in self.objects_tree:
                self.objects_tree[cls_name] = OrderedDict()
            self.objects_tree[cls_name][obj_name] = tpo_obj

            inter_cls_ = PpoLightSignalCi
            inter_obj = inter_cls_()
            inter_obj.tag = obj_name + "_Ci"
            self.objects_tree["PpoLightSignalCi"][inter_obj.tag] = inter_obj

        elif cls_name == "PpoRoutePointer":
            tpo_cls_ = PpoRoutePointer
            tpo_obj = tpo_cls_()
            tpo_obj.tag = obj_name
            if cls_name not in self.objects_tree:
                self.objects_tree[cls_name] = OrderedDict()
            self.objects_tree[cls_name][obj_name] = tpo_obj

            inter_cls_ = PpoRoutePointerRi
            inter_obj = inter_cls_()
            inter_obj.tag = obj_name + "_Ri"
            self.objects_tree["PpoRoutePointerRi"][inter_obj.tag] = inter_obj

        elif cls_name == "PpoAutomaticBlockingSystem":
            tpo_cls_ = PpoAutomaticBlockingSystem
            tpo_obj = tpo_cls_()
            tpo_obj.tag = obj_name
            if cls_name not in self.objects_tree:
                self.objects_tree[cls_name] = OrderedDict()
            self.objects_tree[cls_name][obj_name] = tpo_obj

            inter_cls_ = PpoAutomaticBlockingSystemRi
            inter_obj = inter_cls_()
            inter_obj.tag = obj_name + "_Ri"
            self.objects_tree["PpoAutomaticBlockingSystemRi"][inter_obj.tag] = inter_obj

        elif cls_name == "PpoSemiAutomaticBlockingSystem":
            tpo_cls_ = PpoSemiAutomaticBlockingSystem
            tpo_obj = tpo_cls_()
            tpo_obj.tag = obj_name
            if cls_name not in self.objects_tree:
                self.objects_tree[cls_name] = OrderedDict()
            self.objects_tree[cls_name][obj_name] = tpo_obj

            inter_cls_ = PpoSemiAutomaticBlockingSystemRi
            inter_obj = inter_cls_()
            inter_obj.tag = obj_name + "_Ri"
            self.objects_tree["PpoSemiAutomaticBlockingSystemRi"][inter_obj.tag] = inter_obj

        elif cls_name == "PpoTrackCrossroad":
            first_symbols = obj_name[:2]
            if first_symbols not in self.name_to_obj_dict:
                crossing_cls_ = PpoRailCrossing
                crossing_obj = crossing_cls_()
                crossing_obj.tag = first_symbols
                self.objects_tree["PpoRailCrossing"][crossing_obj.tag] = crossing_obj

                ri_crossing_cls_ = PpoRailCrossingRi
                ri_crossing_obj = ri_crossing_cls_()
                ri_crossing_obj.tag = first_symbols + "_Ri"
                self.objects_tree["PpoRailCrossingRi"][ri_crossing_obj.tag] = ri_crossing_obj

            cls_ = PpoTrackCrossroad
            obj = cls_()
            obj.tag = obj_name
            self.objects_tree["PpoTrackCrossroad"][obj_name] = obj
        else:
            cls_: Type[PpoObject] = eval(cls_name)
            obj = cls_()
            obj.tag = obj_name
            if cls_name not in self.objects_tree:
                self.objects_tree[cls_name] = OrderedDict()
            self.objects_tree[cls_name][obj_name] = obj

    def init_classes(self):
        self.objects_tree = OrderedDict()
        self.objects_tree["    "] = OrderedDict()
        self.objects_tree["      INTERFACE OBJECTS"] = OrderedDict()
        self.objects_tree["     "] = OrderedDict()
        self.objects_tree["PpoLightSignalCi"] = OrderedDict()
        self.objects_tree["PpoLightSignalRi"] = OrderedDict()
        self.objects_tree["PpoRoutePointerRi"] = OrderedDict()
        self.objects_tree["PpoAutomaticBlockingSystemRi"] = OrderedDict()
        self.objects_tree["PpoSemiAutomaticBlockingSystemRi"] = OrderedDict()
        self.objects_tree["PpoRailCrossingRi"] = OrderedDict()
        self.objects_tree["PpoTrainNotificationRi"] = OrderedDict()
        self.objects_tree["PpoControlDeviceDerailmentStockCi"] = OrderedDict()
        self.objects_tree["PpoTrackReceiverRi"] = OrderedDict()
        self.objects_tree["   "] = OrderedDict()
        self.objects_tree[" "] = OrderedDict()
        self.objects_tree["      TECHNOLOGY OBJECTS"] = OrderedDict()
        self.objects_tree["  "] = OrderedDict()
        for cls_name in self.tpl_dict:
            self.objects_tree[cls_name] = OrderedDict()
        self.objects_tree["PpoControlDeviceDerailmentStock"] = OrderedDict()
        self.objects_tree["PpoTrackUnit"] = OrderedDict()
        self.objects_tree["PpoTrackCrossroad"] = OrderedDict()
        self.objects_tree["PpoRailCrossing"] = OrderedDict()

    def init_descriptor_links(self):
        PpoRoutePointer.routePointer.possible_values = self.objects_tree["PpoRoutePointerRi"].keys()

        PpoTrainSignal.routePointer.possible_values = self.objects_tree["PpoRoutePointerRi"].keys()
        PpoTrainSignal.groupRoutePointers.possible_values = self.objects_tree["PpoRoutePointerRi"].keys()
        PpoTrainSignal.uksps.possible_values = self.objects_tree["PpoControlDeviceDerailmentStock"].keys()

        for cls in [PpoAnDtrack, PpoTrackAnDwithPoint, PpoLineEnd, PpoPointSection, PpoTrackSection]:
            cls.trackUnit.possible_values = self.objects_tree["PpoTrackUnit"].keys()

        PpoPoint.section.possible_values = self.objects_tree["PpoPointSection"].keys()
        PpoPoint.autoReturn.possible_values = ["60", "180"]
        PpoPoint.guardPlusPlus.possible_values = self.objects_tree["PpoPoint"].keys()
        PpoPoint.guardPlusMinus.possible_values = self.objects_tree["PpoPoint"].keys()
        PpoPoint.guardMinusPlus.possible_values = self.objects_tree["PpoPoint"].keys()
        PpoPoint.guardMinusMinus.possible_values = self.objects_tree["PpoPoint"].keys()
        PpoPoint.lockingPlus.possible_values = self.objects_tree["PpoPointSection"].keys()
        PpoPoint.lockingMinus.possible_values = self.objects_tree["PpoPointSection"].keys()
        AdditionalSwitch.point.possible_values = self.objects_tree["PpoPoint"].keys()
        AdditionalSwitch.selfPosition.possible_values = ["+", "-"]
        AdditionalSwitch.dependencePosition.possible_values = ["+", "-"]
        PpoPoint.pairPoint.possible_values = self.objects_tree["PpoPoint"].keys()
        SectionAndIgnoreCondition.section.possible_values = self.objects_tree["PpoPointSection"].keys()
        SectionAndIgnoreCondition.point.possible_values = self.objects_tree["PpoPoint"].keys()
        SectionAndIgnoreCondition.position.possible_values = ["+", "-"]

        PpoSemiAutomaticBlockingSystem.isInvitationSignalOpeningBefore.possible_values = ["false"]
        PpoAutomaticBlockingSystem.isInvitationSignalOpeningBefore.possible_values = ["true", "false"]
        PpoAutomaticBlockingSystem.singleTrack.possible_values = ["Yes", "No"]
        PpoAutomaticBlockingSystemRi.adjEnterSig.possible_values = self.objects_tree["PpoLightSignalRi"].keys()

        PpoTrackCrossroad.railCrossing.possible_values = self.objects_tree["PpoRailCrossingRi"].keys()
        PpoTrackCrossroad.iObjTag.possible_values = self.objects_tree["PpoTrainNotificationRi"].keys()

        PpoControlDeviceDerailmentStockCi.enterSignal.possible_values = self.objects_tree["PpoTrainSignal"].keys()

        PpoTrackUnit.iObjsTag.possible_values = set(self.objects_tree["PpoTrackSection"].keys()) | \
                                                set(self.objects_tree["PpoPointSection"].keys()) | \
                                                set(self.objects_tree["PpoTrackAnDwithPoint"].keys()) | \
                                                set(self.objects_tree["PpoAnDtrack"].keys())
        PpoTrackUnit.evenTag.possible_values = self.objects_tree["PpoTrackEncodingPoint"].keys()
        PpoTrackUnit.oddTag.possible_values = self.objects_tree["PpoTrackEncodingPoint"].keys()

        PpoTrackAnDwithPoint.directionPointAnDTrack.possible_values = ["Direction12", "Direction21"]
        PpoTrackAnDwithPoint.oppositeTrackAnDwithPoint.possible_values = self.objects_tree["PpoTrackAnDwithPoint"].keys()



    def init_objects(self):
        self.init_classes()
        self.init_descriptor_links()
        for cls_name in self.tpl_dict:
            for obj_name in self.tpl_dict[cls_name]:
                self.init_object(cls_name, obj_name)
        self.send_objects_tree.emit(self.str_objects_tree)

    def init_bounded_tpl_descriptors(self):
        pass

    def init_bounded_obj_id_descriptors(self):
        ru_list = self.obj_id_dict["RU"]
        for subclass in PpoObject.__subclasses__():
            if hasattr(subclass, "idControlArea"):
                descr: StrBoundedValuesDescriptor = getattr(subclass, "idControlArea")
                descr.possible_values = ru_list

    def file_tpl_got(self, d: OrderedDict[str, list[str]]):
        # print("tpl_got")
        self.bool_tpl_got = True
        check_not_repeating_names(d)
        self.tpl_dict = d
        if self.bool_obj_id_got:
            self.compare()
        self.init_bounded_tpl_descriptors()

        self.init_objects()

    def file_obj_id_got(self, d: OrderedDict[str, list[str]]):
        # print("obj_id_got")
        self.bool_obj_id_got = True
        check_not_repeating_names(d)
        self.obj_id_dict = d
        if self.bool_tpl_got:
            self.compare()
        self.init_bounded_obj_id_descriptors()
        if self.current_object:
            self.got_object_name(self.current_object.tag)

    def compare(self):
        differences = {'tpl': [], 'obj_id': []}

        # cycle of append
        for cls_name in self.tpl_dict:
            if cls_name in tpl_to_obj_id:
                tpl_list = self.tpl_dict[cls_name]
                obj_id_list = self.obj_id_dict[tpl_to_obj_id[cls_name]]
                for tag in tpl_list:
                    if (cls_name, tag) not in differences['tpl']:
                        differences['tpl'].append((cls_name, tag))
                for tag in obj_id_list:
                    if (tpl_to_obj_id[cls_name], tag) not in differences['obj_id']:
                        differences['obj_id'].append((tpl_to_obj_id[cls_name], tag))

        # cycle of remove
        for cls_name in self.tpl_dict:
            if cls_name in tpl_to_obj_id:
                tpl_list = self.tpl_dict[cls_name]
                obj_id_list = self.obj_id_dict[tpl_to_obj_id[cls_name]]
                for tag in tpl_list:
                    if (tpl_to_obj_id[cls_name], tag) in differences['obj_id']:
                        differences['obj_id'].remove((tpl_to_obj_id[cls_name], tag))
                for tag in obj_id_list:
                    if (cls_name, tag) in differences['tpl']:
                        differences['tpl'].remove((cls_name, tag))

        print("Differences between tpl and objects_id")
        print("Tpl:")
        for elem in differences['tpl']:
            print(elem)
        print("Obj_id:")
        for elem in differences['obj_id']:
            print(elem)

    def attr_changed(self, address: list, new_attr_value: str):
        # print("attr changed", address, new_attr_value)
        obj = self.current_object
        for elem in address:
            attr_name = elem[0]
            index = elem[1]
            descr = getattr(obj.__class__, attr_name)
            if isinstance(descr, ObjectListDescriptor):
                obj_list = getattr(obj, attr_name)
                obj = obj_list[index]
            elif isinstance(descr, StrBoundedValuesDescriptor):
                if descr.is_list:
                    assert index != -1, "Index should be != -1"
                    old_list = copy(getattr(obj, attr_name))
                    old_list[index] = new_attr_value
                    setattr(obj, attr_name, old_list)
                else:
                    assert index == -1, "Index should be == -1"
                    setattr(obj, attr_name, new_attr_value)
            else:
                assert index == -1, "Index should be == -1"
                setattr(obj, attr_name, new_attr_value)
        self.got_object_name(self.current_object.tag)

    def add_attrib_list_element(self, address: list):
        # print("add_attrib_list", address)
        obj = self.current_object
        for i, elem in enumerate(address):
            attr_name = elem[0]
            index = elem[1]
            descr = getattr(obj.__class__, attr_name)
            # not last index handling
            if i < len(address) - 1:
                assert isinstance(descr, ObjectListDescriptor), "Internal index only for ObjectListDescriptor"
                obj_list = getattr(obj, attr_name)
                obj = obj_list[index]
                continue
            # last index handling
            assert index == -1, "Index should be == -1"
            if isinstance(descr, ObjectListDescriptor):
                new_item = descr.obj_type()
            elif isinstance(descr, StrBoundedValuesDescriptor):
                new_item = ""
            else:
                raise NotImplementedError("NotImplementedError")
            old_list = copy(getattr(obj, attr_name))
            old_list.append(new_item)
            setattr(obj, attr_name, old_list)
        self.got_object_name(self.current_object.tag)

    def remove_attrib_list_element(self, address: list):
        # print("remove_attrib_list", address)
        obj = self.current_object
        for i, elem in enumerate(address):
            attr_name = elem[0]
            index = elem[1]
            descr = getattr(obj.__class__, attr_name)
            # not last index handling
            if i < len(address) - 1:
                assert isinstance(descr, ObjectListDescriptor), "Internal index only for ObjectListDescriptor"
                obj_list = getattr(obj, attr_name)
                obj = obj_list[index]
                continue
            # last index handling
            assert index != -1, "Index should be != -1"
            old_list = copy(getattr(obj, attr_name))
            old_list.pop(index)
            setattr(obj, attr_name, old_list)
            self.got_object_name(self.current_object.tag)

    def got_change_cls_request(self, obj_name: str, to_cls_name: str):
        # 1. create new obj in new class
        new_name = self.got_add_new(to_cls_name)
        # 2. remove obj in old class
        self.got_remove_object_request(obj_name)
        # 3. rename obj in new class
        self.got_rename(new_name, obj_name)

        self.send_objects_tree.emit(self.str_objects_tree)

    def got_remove_object_request(self, name: str):
        cls_name = self.obj_name_to_cls_name_dict[name]
        self.objects_tree[cls_name].pop(name)

        self.send_objects_tree.emit(self.str_objects_tree)

    def got_add_new(self, cls_name: str) -> str:
        i = 1
        while True:
            name_candidate = "{}_{}".format(cls_name, i)
            if name_candidate not in self.name_to_obj_dict:
                break
            i += 1
        self.init_object(cls_name, name_candidate)
        self.send_objects_tree.emit(self.str_objects_tree)
        return name_candidate

    def got_rename(self, old_name: str, new_name: str):
        if new_name in self.name_to_obj_dict:
            self.rename_rejected(old_name, new_name)
            self.send_objects_tree.emit(self.str_objects_tree)
        else:
            obj = self.name_to_obj_dict[old_name]
            obj.tag = new_name

            cls_name = self.obj_name_to_cls_name_dict[old_name]
            keys_list = list(self.objects_tree[cls_name].keys())
            index = keys_list.index(old_name)
            self.objects_tree[cls_name][new_name] = obj
            for key_index in range(index, len(keys_list)):
                self.objects_tree[cls_name].move_to_end(keys_list[key_index])
            self.objects_tree[cls_name].pop(old_name)
            self.send_objects_tree.emit(self.str_objects_tree)

    def rename_rejected(self, old_name: str, new_name: str):
        print("Rename from {} to {} rejected, name already exists".format(old_name, new_name))

    def generate_file(self, file_name: str):
        if file_name == "TObjectsPoint":
            object_names = self.objects_tree["PpoPoint"]
            objects = [self.name_to_obj_dict[object_name] for object_name in object_names]
            obj_jsons = [obj.to_json for obj in objects]
            with open(os.path.join("output", "config", "{}.json".format(file_name)), "w") as write_file:
                json.dump(obj_jsons, write_file, indent=4)

    def got_object_name(self, name: str):

        if name in self.obj_name_to_cls_name_dict:
            obj = self.name_to_obj_dict[name]

            # 1. rollback handling
            if not (self.current_object is obj):
                for attr_name in obj.data.keys():
                    if attr_name == "id":
                        attr_name += "_"
                    descr = getattr(obj.__class__, attr_name)
                    if isinstance(descr, DefaultDescriptor):
                        last_accepted_value = getattr(obj, "_{}".format(attr_name))
                        setattr(obj, attr_name, last_accepted_value)
                    # if isinstance(descr, StrBoundedValuesDescriptor):
                    #     last_accepted_value = getattr(obj, "_{}".format(attr_name))
                    #     setattr(obj, attr_name, last_accepted_value)

            # 2. main handling
            self.current_object = obj
            self.send_attrib_list.emit(self.form_columns(obj))

    def form_columns(self, obj: PpoObject) -> list:
        result_data = []
        title_label = LabelInfo()
        title_label.is_centered = True
        title_label.current_value = obj.tag
        result_data.append([title_label.to_tuple()])
        for attr_name in obj.data.keys():
            result_data.extend(self.form_attrib(obj, attr_name))
        return result_data

    def form_attrib(self, obj: PpoObject, attr_name: str, current_address: list = None) -> list:
        if not current_address:
            current_address = []
        result = []
        if attr_name in ["addrUI_KS", "output_SNK", "notificationPoints", "output_DSO", "adjEnterSig"]:
            result.append([("Spacing", "20")])
        if attr_name == "id":
            attr_name += "_"
        descr = getattr(obj.__class__, attr_name)
        if isinstance(descr, StrBoundedValuesDescriptor):
            if descr.is_list:
                label = LabelInfo()
                label.is_centered = False
                label.current_value = attr_name

                ca = copy(current_address)
                ca.append((attr_name, -1))
                add_btn = ButtonInfo()
                add_btn.is_add_button = True
                add_btn.attr_name = attr_name
                add_btn.address = ca
                result.append([label.to_tuple(), add_btn.to_tuple()])

                attr_values = getattr(obj, attr_name)
                attr_check_statuses = getattr(obj, "_check_status_{}".format(attr_name))
                for i, attr_value in enumerate(attr_values):
                    ca = copy(current_address)
                    ca.append((attr_name, i))

                    lineEdit = LineEditInfo()
                    lineEdit.possible_values = descr.possible_values
                    lineEdit.current_value = attr_value
                    lineEdit.check_status = attr_check_statuses[i]
                    lineEdit.attr_name = attr_name
                    lineEdit.index = i
                    lineEdit.address = ca

                    remove_button = ButtonInfo()
                    remove_button.is_add_button = False
                    remove_button.attr_name = attr_name
                    remove_button.index = i
                    remove_button.address = ca
                    result.append([lineEdit.to_tuple(), remove_button.to_tuple()])
            else:
                ca = copy(current_address)
                ca.append((attr_name, -1))
                label = LabelInfo()
                label.is_centered = False
                label.current_value = attr_name

                lineEdit = LineEditInfo()
                lineEdit.possible_values = descr.possible_values
                lineEdit.current_value = getattr(obj, attr_name)
                lineEdit.check_status = getattr(obj, "_check_status_{}".format(attr_name))
                lineEdit.attr_name = attr_name
                lineEdit.address = ca
                result.append([label.to_tuple(), lineEdit.to_tuple()])

        elif isinstance(descr, ObjectListDescriptor):
            title_label = LabelInfo()
            title_label.is_centered = True
            title_label.current_value = attr_name

            ca = copy(current_address)
            ca.append((attr_name, -1))
            add_btn = ButtonInfo()
            add_btn.is_add_button = True
            add_btn.attr_name = attr_name
            add_btn.address = ca
            result.append([title_label.to_tuple(), add_btn.to_tuple()])

            internal_objects = getattr(obj, attr_name)
            for i, internal_object in enumerate(internal_objects):
                ca = copy(current_address)
                ca.append((attr_name, i))
                internal_object: PpoObject
                all_attr_names = internal_object.all_attributes
                for local_attr_name in all_attr_names:
                    result.extend(self.form_attrib(internal_object, local_attr_name, ca))
                remove_button = ButtonInfo()
                remove_button.is_add_button = False
                remove_button.attr_name = attr_name
                remove_button.index = i
                remove_button.address = ca
                result.append([remove_button.to_tuple()])
        elif isinstance(descr, DefaultDescriptor):
            attr_check_status = getattr(obj, "_check_status_{}".format(attr_name))

            label = LabelInfo()
            label.is_centered = False
            label.current_value = attr_name

            ca = copy(current_address)
            ca.append((attr_name, -1))
            lineEdit = LineEditInfo()
            lineEdit.current_value = getattr(obj, attr_name)
            lineEdit.check_status = attr_check_status
            lineEdit.address = ca
            result.append([label.to_tuple(), lineEdit.to_tuple()])
        else:
            label = LabelInfo()
            label.is_centered = False
            label.current_value = attr_name

            ca = copy(current_address)
            ca.append((attr_name, -1))
            lineEdit = LineEditInfo()
            lineEdit.current_value = getattr(obj, attr_name)
            lineEdit.address = ca
            result.append([label.to_tuple(), lineEdit.to_tuple()])
        return result


class LineEditInfo:
    def __init__(self):
        self.possible_values = []
        self.current_value = ""
        self.check_status = ""
        self.attr_name = ""
        self.address = []
        self.index = -1

    def to_tuple(self) -> tuple[str, OrderedDict[str, Any]]:
        result = OrderedDict()
        result["possible_values"] = self.possible_values
        result["current_value"] = self.current_value
        result["check_status"] = self.check_status
        result["attr_name"] = self.attr_name
        result["index"] = self.index
        result["address"] = self.address
        return "LineEdit", result


class LabelInfo:
    def __init__(self):
        self.is_centered = True
        self.current_value = ""

    def to_tuple(self) -> tuple[str, OrderedDict[str, Any]]:
        result = OrderedDict()
        result["is_centered"] = self.is_centered
        result["current_value"] = self.current_value
        return "Label", result


class ButtonInfo:
    def __init__(self):
        self.is_add_button = True
        self.attr_name = ""
        self.address = []
        self.index = -1

    def to_tuple(self) -> tuple[str, OrderedDict[str, Any]]:
        result = OrderedDict()
        result["is_add_button"] = self.is_add_button
        result["attr_name"] = self.attr_name
        result["index"] = self.index
        result["address"] = self.address
        return "Button", result


if __name__ == '__main__':
    test_1 = False
    if test_1:
        pass
        # cell_obj = CompositeObjectCell()
        # cell_1 = ElementaryObjectCell()
        # cell_1.input_value = 1
        # cell_2 = ElementaryObjectCell()
        # cell_2.input_value = 2
        # cell_3 = ElementaryObjectCell()
        # cell_3.input_value = 3
        # cell_4 = ElementaryObjectCell()
        # cell_4.input_value = 4
        # cell_obj.mapping["1"] = cell_1
        # cell_obj.mapping["2"] = cell_2
        # cell_list = ListCell()
        # cell_list.cells.append(cell_3)
        # cell_list.cells.append(cell_4)
        # cell_obj.mapping["list"] = cell_list
        #
        # for row in cell_obj.view():
        #     print(row)
    test_2 = True
    if test_2:
        additSw = AdditionalSwitch()
        print(additSw.all_attributes)
