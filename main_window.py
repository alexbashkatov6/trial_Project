import os
import re
import time
from functools import partial

from PyQt5.QtWidgets import QWidgetItem, QMainWindow, QTextEdit, QAction, QToolBar, QPushButton, QHBoxLayout, \
    QVBoxLayout, QLabel, QGridLayout, QWidget, QLayout, QLineEdit, QSplitter, QComboBox, QTreeView, QToolTip, QMenu
from PyQt5.QtGui import QIcon, QPainter, QPen, QValidator, QMouseEvent, QFocusEvent, QContextMenuEvent, QFont, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QRect, QPoint, QEvent, QTimer
from PyQt5.Qt import QStandardItemModel, QStandardItem, qApp

from nv_attribute_format import AttributeFormat
from nv_config import CLASSES_SEQUENCE, GROUND_CS_NAME, PICTURE_FOLDER
# from nv_attributed_objects import BSSObjectStatus


class ToolBarOfClasses(QToolBar):

    send_class_name = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.pic_names_sorted_list = None
        self.qb_list = []

    def extract_pictures(self, classes_names):
        root_path = os.getcwd()
        tree = os.walk(root_path + '\\' + PICTURE_FOLDER)
        self.pic_names_sorted_list = []
        extracted_pict_names = []
        for d, dirs, files in tree:
            for file in files:
                file_without_extent = file[:file.rfind('.')]
                assert file_without_extent in classes_names, \
                    'Picture name {} not found in classes names list'.format(file_without_extent)
                extracted_pict_names.append(file_without_extent)
        self.pic_names_sorted_list = [i for i in CLASSES_SEQUENCE if i in extracted_pict_names]

    def construct_widget(self, min_size):
        self.setMinimumSize(min_size, min_size)
        for pic_name in self.pic_names_sorted_list:
            icon = QIcon('{}/{}.jpg'.format(PICTURE_FOLDER, pic_name))
            qb = QPushButton(icon, '')
            qb.setIconSize(QSize(min_size, min_size))
            qb.setToolTip(pic_name[pic_name.find('_') + 1:])
            qb.clicked.connect(self.act_triggered)
            self.qb_list.append(qb)
            self.addWidget(qb)

    def act_triggered(self):
        sender = self.sender()
        cls_name = self.pic_names_sorted_list[self.qb_list.index(sender)]
        self.send_class_name.emit(cls_name)


class AttribColumn(QWidget):
    new_name_value_ac = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        # self.main_layout = QVBoxLayout()
        # self.setLayout(self.main_layout)
        # self.widgets_dict: dict[QWidget, QWidget] = {}

    def clean(self):
        if hasattr(self, 'column'):
            for child in self.column.children():
                child.setParent(None)
            self.column.setParent(None)
        self.column = QWidget(self)
        self.main_layout.addWidget(self.column)
        self.column_layout = QVBoxLayout()
        self.column.setLayout(self.column_layout)
        self.widgets_dict = {}

        # layout_stack = [self.main_layout]
        # while layout_stack:
        #     current_layout = layout_stack.pop()
        #     count = current_layout.count()
        #     wgts = set()
        #     for index in range(count):
        #         item = current_layout.itemAt(index)
        #         if isinstance(item, QLayout):
        #             layout_stack.append(item)
        #         elif isinstance(item, QWidgetItem):
        #             wgt = item.widget()
        #             wgts.add(wgt)
        #         else:
        #             assert False, 'Other variants'
        #     for wgt in wgts:
        #         wgt.setParent(None)
        #     if not (current_layout is self.main_layout):
        #         current_layout.setParent(None)

    def init_from_container(self, af_list):
        self.clean()
        for af in af_list:
            attr_layout = QHBoxLayout()
            if af.attr_type == 'title':
                attr_layout.addWidget(QLabel(af.attr_name, self.column))
            if af.attr_type == 'splitter':
                name_wgt = QLabel(af.attr_name, self.column)
                attr_layout.addWidget(name_wgt)
                value_wgt = QComboBox(self.column)
                value_wgt.addItems(af.possible_values)
                value_wgt.setCurrentText(af.attr_value)
                value_wgt.currentTextChanged.connect(self.changed_value)
                attr_layout.addWidget(value_wgt)
                self.widgets_dict[value_wgt] = name_wgt
            if af.attr_type == 'str_value':
                name_wgt_0 = QLabel(af.attr_name, self.column)
                name_wgt_0.setToolTip(af.req_type_str)
                attr_layout.addWidget(name_wgt_0)
                value_wgt_0 = QLineEdit(af.attr_value, self.column)
                self.set_bool_color(value_wgt_0, af)
                value_wgt_0.setToolTip(af.status_check)
                value_wgt_0.returnPressed.connect(self.edit_finished)
                value_wgt_0.textEdited.connect(self.color_reset)
                attr_layout.addWidget(value_wgt_0)
                self.widgets_dict[value_wgt_0] = name_wgt_0
            self.column_layout.addLayout(attr_layout)

    @pyqtSlot()
    def edit_finished(self):
        sender = self.sender()
        label: QLabel = self.widgets_dict[sender]
        self.new_name_value_ac.emit(label.text(), sender.text())

    @pyqtSlot(str)
    def changed_value(self, new_val: str):
        sender = self.sender()
        label: QLabel = self.widgets_dict[sender]
        self.new_name_value_ac.emit(label.text(), new_val)

    @pyqtSlot(str)
    def color_reset(self, new_val: str):
        sender = self.sender()
        sender.setStyleSheet("background-color: white")

    @staticmethod
    def set_bool_color(le: QLineEdit, af: AttributeFormat):
        if af.attr_value == '':
            le.setStyleSheet("background-color: white")
        elif af.status_check:
            le.setStyleSheet("background-color: red")
        elif af.is_suggested:
            le.setStyleSheet("background-color: yellow")
        else:
            le.setStyleSheet("background-color: green")


class ToolBarOfAttributes(QToolBar):
    new_name_value_tb = pyqtSignal(str, str)
    apply_clicked = pyqtSignal()

    def __init__(self, min_size):
        super().__init__()
        self.setMinimumSize(min_size, min_size)
        self.wgt_main = QWidget()
        self.addWidget(self.wgt_main)

        self.active_class_label = QLabel('< pick tool >', self)
        self.active_class_label.setAlignment(Qt.AlignHCenter)

        self.attributes_column = AttribColumn(self)

        self.apply_button = QPushButton('Create/Apply', self)
        self.apply_button.setEnabled(False)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.active_class_label)
        self.vbox.addWidget(self.attributes_column)
        self.vbox.addWidget(self.apply_button)
        self.wgt_main.setLayout(self.vbox)

        self.attributes_column.new_name_value_ac.connect(self.new_name_value_tb)
        self.apply_button.clicked.connect(self.apply_clicked)

    @pyqtSlot(list)
    def set_attr_struct(self, af_list):
        self.attributes_column.init_from_container(af_list)

    @pyqtSlot(str)
    def set_class_str(self, class_str):
        self.active_class_label.setText(class_str)

    @pyqtSlot(bool)
    def set_active_apply(self, active_apply):
        self.apply_button.setEnabled(active_apply)

    @pyqtSlot(str)
    def set_focus_widget_value(self, obj_name_str):
        focus_widget = self.focusWidget()
        if isinstance(focus_widget, QLineEdit):
            focus_widget: QLineEdit
            focus_widget.setText(obj_name_str)
            focus_widget.returnPressed.emit()


class CustomTW(QTreeView):
    send_data_fill = pyqtSignal(str)
    send_data_edit = pyqtSignal(str)
    send_data_right_click = pyqtSignal(str)
    send_data_hover = pyqtSignal(str)
    send_data_pick = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(False)
        self.timer = QTimer(self)
        self.first_timer_notification = True
        self.millisecs_of_notification = 1000
        self.obj_hovered_name = ''
        self.current_cursor_point = QPoint(0, 0)
        self.timer_double_click = QTimer(self)
        self.double_click = False
        self.data_release = None
        self.timer_double_click.timeout.connect(self.release_data_emit)

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:

        if a0.button() == Qt.RightButton:
            data = self.indexAt(a0.localPos().toPoint()).data()
            if not (data is None):
                self.send_data_right_click.emit(data)
        if a0.button() == Qt.LeftButton:
            data = self.indexAt(a0.localPos().toPoint()).data()
            if data in CLASSES_SEQUENCE:
                super().mouseReleaseEvent(a0)
                return
            if self.double_click:
                self.timer_double_click.stop()
                self.double_click = False
            elif not self.timer_double_click.isActive():
                self.timer_double_click.start(qApp.doubleClickInterval())
                self.data_release = data

    def mousePressEvent(self, a0: QMouseEvent) -> None:

        if a0.button() == Qt.LeftButton:
            data = self.indexAt(a0.localPos().toPoint()).data()
            if (data in CLASSES_SEQUENCE) or (data is None):
                super().mousePressEvent(a0)
                return
            if self.timer_double_click.isActive():
                self.double_click = True
                self.send_name_fill(self.data_release)

    def release_data_emit(self):
        if not (self.data_release is None):
            self.send_data_pick.emit(self.data_release)
            self.timer_double_click.stop()

    def mouseMoveEvent(self, a0: QEvent) -> None:
        self.timer.stop()
        self.timer.timeout.connect(self.timeout_handling)
        self.timer.start(self.millisecs_of_notification)
        self.first_timer_notification = True
        if isinstance(a0, QMouseEvent):
            data = self.indexAt(a0.localPos().toPoint()).data()
            self.current_cursor_point = a0.globalPos()
            if data is None:
                self.obj_hovered_name = ''
            else:
                self.obj_hovered_name = data

    def enterEvent(self, a0: QEvent) -> None:
        self.timer = QTimer(self)

    def leaveEvent(self, a0: QEvent) -> None:
        self.timer.stop()

    @pyqtSlot()
    def timeout_handling(self):
        if self.first_timer_notification:
            self.first_timer_notification = False
            ohn = self.obj_hovered_name
            if ohn and (ohn not in self.parent().class_nodes):
                self.send_data_hover.emit(self.obj_hovered_name)

    def contextMenuEvent(self, a0: QContextMenuEvent):
        data = self.indexAt(a0.pos()).data()
        if data and (data not in self.parent().class_nodes):
            contextMenu = QMenu(self)
            fillAct = contextMenu.addAction("Fill")
            fillAct.triggered.connect(partial(self.send_name_fill, val=self.indexAt(a0.pos())))
            if data != GROUND_CS_NAME:
                editAct = contextMenu.addAction("Edit")
                editAct.triggered.connect(partial(self.send_name_edit, val=self.indexAt(a0.pos())))
                deleteAct = contextMenu.addAction("Delete")

            action = contextMenu.exec_(self.mapToGlobal(a0.pos()))

    def finish_operations(self):
        self.expandAll()

    def send_name_fill(self, val):
        if val is None:
            return
        if type(val) != str:
            val = val.data()
        if val not in self.parent().class_nodes:
            self.send_data_fill.emit(val)

    def send_name_edit(self, val):
        if val.data() not in self.parent().class_nodes:
            self.send_data_edit.emit(val.data())


class ObjectsTree(QWidget):
    send_data_fill = pyqtSignal(str)
    send_data_edit = pyqtSignal(str)
    send_data_right_click = pyqtSignal(str)
    send_data_hover = pyqtSignal(str)
    send_data_pick = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vbox = QVBoxLayout(self)
        self.setLayout(self.vbox)
        self.clean()

    def clean(self):
        self.class_nodes = set()
        if hasattr(self, 'tree_view'):
            self.tree_view.setParent(None)
        self.tree_view = CustomTW(self)
        self.tree_model = QStandardItemModel()
        self.root_node = self.tree_model.invisibleRootItem()
        self.tree_view.setModel(self.tree_model)
        self.vbox.addWidget(self.tree_view)

        self.tree_view.send_data_fill.connect(self.send_data_fill)
        self.tree_view.send_data_edit.connect(self.send_data_edit)
        self.tree_view.send_data_right_click.connect(self.send_data_right_click)
        self.tree_view.send_data_hover.connect(self.send_data_hover)
        self.tree_view.send_data_pick.connect(self.send_data_pick)

    def init_from_graph_tree(self, tree_dict):
        self.clean()
        for class_name in tree_dict:
            item_class = QStandardItem(class_name)
            item_class.setEditable(False)
            item_class.setSelectable(False)
            self.root_node.appendRow(item_class)
            self.class_nodes.add(class_name)
            for obj_name, obj_pick_status, obj_corrupt_status in tree_dict[class_name]:
                item_obj = QStandardItem(obj_name)
                item_obj.setEditable(False)
                item_class.appendRow(item_obj)

                if obj_pick_status == 'p_default':
                    item_obj.setData(QColor('white'), Qt.BackgroundColorRole)
                if obj_pick_status == 'picked':
                    item_obj.setData(QColor('green'), Qt.BackgroundColorRole)
                if obj_pick_status == 'pick_directly_dependent':
                    item_obj.setData(QColor('greenyellow'), Qt.BackgroundColorRole)
                if obj_pick_status == 'pick_indirectly_dependent':
                    item_obj.setData(QColor('yellow'), Qt.BackgroundColorRole)

                if obj_corrupt_status == 'c_default':
                    item_obj.setData(QColor('black'), Qt.ForegroundRole)
                if obj_corrupt_status == 'corrupted':
                    item_obj.setData(QColor('red'), Qt.ForegroundRole)
                if obj_corrupt_status == 'corrupt_dependent':
                    item_obj.setData(QColor('orange'), Qt.ForegroundRole)
        self.tree_view.finish_operations()


class ToolBarOfObjects(QToolBar):
    send_data_fill = pyqtSignal(str)
    send_data_edit = pyqtSignal(str)
    send_data_right_click = pyqtSignal(str)
    send_data_hover = pyqtSignal(str)
    send_data_pick = pyqtSignal(str)
    send_leave = pyqtSignal()

    def __init__(self, min_size):
        super().__init__()
        self.setMinimumSize(min_size, min_size)
        self.wgt_main = QWidget(self)
        self.addWidget(self.wgt_main)

        self.title_label = QLabel('Tree of objects', self)
        self.title_label.setAlignment(Qt.AlignHCenter)

        self.objects_tree = ObjectsTree(self)

        self.vbox = QVBoxLayout(self)
        self.vbox.addWidget(self.title_label)
        self.vbox.addWidget(self.objects_tree)
        self.wgt_main.setLayout(self.vbox)

        self.objects_tree.send_data_fill.connect(self.send_data_fill)
        self.objects_tree.send_data_edit.connect(self.send_data_edit)
        self.objects_tree.send_data_right_click.connect(self.send_data_right_click)
        self.objects_tree.send_data_hover.connect(self.send_data_hover)
        self.objects_tree.send_data_pick.connect(self.send_data_pick)

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            if a0.source() == 0:
                self.send_leave.emit()

    @pyqtSlot(dict)
    def set_tree(self, tree_dict):
        self.objects_tree.init_from_graph_tree(tree_dict)

    @pyqtSlot(list)
    def show_info_about_object(self, af_list):
        result_str = ''
        for af in af_list:
            if af.attr_type == 'title':
                result_str += '{}\n'.format(af.attr_name)
            if (af.attr_type == 'splitter') or (af.attr_type == 'str_value'):
                result_str += '{}: {}\n'.format(af.attr_name, af.attr_value)
        QToolTip.showText(self.objects_tree.tree_view.current_cursor_point, result_str.rstrip())


class PaintingArea(QWidget):
    def __init__(self, min_size):
        super().__init__()
        self.setMinimumSize(min_size, min_size)


class MW(QMainWindow):

    def __init__(self):
        super().__init__()

        # widgets params
        top_toolbar_min_height_width = 50
        painting_area_min_height_width = 500
        right_toolbar_min_height_width = 250
        left_toolbar_min_height_width = 250

        # central wgt
        self.pa = PaintingArea(painting_area_min_height_width)
        self.setCentralWidget(self.pa)
        # self.qp = QPainter()
        # pen = QPen(Qt.black, 2, Qt.SolidLine)
        # self.qp.begin(self) #.pa
        # self.qp.setPen(pen)
        # self.qp.drawLine(400, 400, 500, 500)
        # self.qp.end()

        # ce
        # self.ce = ce.CurrentEdit()

        # Top tool bar format
        self.ttb = ToolBarOfClasses()
        # self.ttb.extract_pictures(self.ce.extractedClasses)
        self.ttb.extract_pictures(CLASSES_SEQUENCE)
        self.ttb.construct_widget(top_toolbar_min_height_width)

        # Right tool bar format
        self.rtb = ToolBarOfAttributes(right_toolbar_min_height_width)

        # Left tool bar format
        self.ltb = ToolBarOfObjects(left_toolbar_min_height_width)

        self.addToolBar(Qt.TopToolBarArea, self.ttb)
        self.addToolBar(Qt.RightToolBarArea, self.rtb)
        self.addToolBar(Qt.LeftToolBarArea, self.ltb)

        self.statusBar()

        menubar = self.menuBar()
        menubar.addMenu('&File')  # fileMenu =

        self.setGeometry(50, 50, 550, 450)
        self.setWindowTitle('Main window')
        self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        qp.setPen(pen)
        pnt_1 = QPoint(400, 200)
        pnt_2 = QPoint(500, 500)
        pnt_3 = QPoint(400, 300)
        qp.drawLine(pnt_1, pnt_2)
        qp.drawLine(pnt_1, pnt_3)
        qp.drawEllipse(pnt_1, 100, 100)
        qp.end()
