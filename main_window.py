import os
import re

from PyQt5.QtWidgets import QWidgetItem, QMainWindow, QTextEdit, QAction, QToolBar, QPushButton, QHBoxLayout, \
    QVBoxLayout, QLabel, QGridLayout, QWidget, QLayout, QLineEdit, QSplitter, QComboBox, QTreeView
from PyQt5.QtGui import QIcon, QPainter, QPen, QValidator
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QRect, QPoint
from PyQt5.Qt import QStandardItemModel, QStandardItem

from nv_attribute_format import AttributeFormat


class ToolBarOfClasses(QToolBar):

    send_class_name = pyqtSignal(str)
    picFolder = 'pictures'

    def __init__(self):
        super().__init__()
        self.pic_names_sorted_list = None
        self.qb_list = []

    def extract_pictures(self, classes_names):
        pic_names = {}
        nums_of_pict = []
        root_path = os.getcwd()
        tree = os.walk(root_path + '\\' + self.picFolder)
        for d, dirs, files in tree:
            for file in files:
                file_without_extent = file[:file.rfind('.')]
                assert bool(re.fullmatch(r'\d{2}_\w+', file_without_extent)), \
                    'File of picture should be in format (d)(d)_(className), given {}'.format(file_without_extent)
                file_prefix = file_without_extent[:file_without_extent.find('_')]
                file_postfix = file_without_extent[file_without_extent.find('_') + 1:]
                int_prefix = int(file_prefix)
                assert int_prefix not in nums_of_pict, 'Num of pic file {} is repeating'.format(int_prefix)
                nums_of_pict.append(int_prefix)
                assert file_postfix in classes_names, \
                    'Class not found in file_postfix {}'.format(file_without_extent)
                pic_names[int_prefix] = file_without_extent
        self.pic_names_sorted_list = [pic_names[i] for i in sorted(pic_names)]

    def construct_widget(self, min_size):
        self.setMinimumSize(min_size, min_size)
        for pic_name in self.pic_names_sorted_list:
            icon = QIcon('{}/{}.jpg'.format(self.picFolder, pic_name))
            qb = QPushButton(icon, '')
            qb.setIconSize(QSize(min_size, min_size))
            qb.setToolTip(pic_name[pic_name.find('_') + 1:])
            qb.clicked.connect(self.act_triggered)
            self.qb_list.append(qb)
            self.addWidget(qb)

    def act_triggered(self):
        sender = self.sender()
        long_name = self.pic_names_sorted_list[self.qb_list.index(sender)]
        self.send_class_name.emit(long_name[long_name.index('_') + 1:])


class AttribColumn(QWidget):
    new_name_value_ac = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.widgets_dict: dict[QWidget, QWidget] = {}

    def clean(self):
        layout_stack = [self.main_layout]
        while layout_stack:
            current_layout = layout_stack.pop()
            count = current_layout.count()
            wgts = set()
            for index in range(count):
                item = current_layout.itemAt(index)
                if isinstance(item, QLayout):
                    layout_stack.append(item)
                elif isinstance(item, QWidgetItem):
                    wgt = item.widget()
                    wgts.add(wgt)
                else:
                    assert False, 'Other variants'
            for wgt in wgts:
                wgt.setParent(None)
        self.widgets_dict = {}

    def init_from_container(self, af_list):
        self.clean()
        for af in af_list:
            attr_layout = QHBoxLayout()
            if af.attr_type == 'title':
                attr_layout.addWidget(QLabel(af.attr_name, self))
            if af.attr_type == 'splitter':
                name_wgt = QLabel(af.attr_name, self)
                attr_layout.addWidget(name_wgt)
                value_wgt = QComboBox(self)
                value_wgt.addItems(af.possible_values)
                value_wgt.setCurrentText(af.attr_value)
                value_wgt.currentTextChanged.connect(self.changed_value)
                attr_layout.addWidget(value_wgt)
                self.widgets_dict[value_wgt] = name_wgt
            if af.attr_type == 'value':
                name_wgt_0 = QLabel(af.attr_name, self)
                name_wgt_0.setToolTip(af.req_type_str)
                attr_layout.addWidget(name_wgt_0)
                value_wgt_0 = QLineEdit(af.attr_value, self)
                self.set_bool_color(value_wgt_0, af)
                value_wgt_0.setToolTip(af.status_check)
                value_wgt_0.returnPressed.connect(self.edit_finished)
                value_wgt_0.textEdited.connect(self.color_reset)
                attr_layout.addWidget(value_wgt_0)
                self.widgets_dict[value_wgt_0] = name_wgt_0
            self.main_layout.addLayout(attr_layout)

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

    # def get_line_edit(self, str_name: str) -> QLineEdit:
    #     for line_edit_widget, label_widget in self.widgets_dict.items():
    #         if label_widget.text() == str_name:
    #             return line_edit_widget
    #     print('Not found')
    #     assert False, 'Not found'
    #
    # def replace_line_edit(self, af: AttributeFormat):
    #     str_name = af.attr_name
    #     old_le = self.get_line_edit(str_name)
    #     new_le = QLineEdit(af.attr_value, self)
    #     self.set_bool_color(new_le, af)
    #     self.main_layout.replaceWidget(old_le, new_le)
    #     self.widgets_dict[new_le] = self.widgets_dict[old_le]
    #     self.widgets_dict.pop(old_le)
    #     old_le.setParent(None)

    @pyqtSlot(str)
    def color_reset(self, new_val: str):
        sender = self.sender()
        sender.setStyleSheet("background-color: white")

    @staticmethod
    def set_bool_color(le: QLineEdit, af: AttributeFormat):
        if af.status_check == 'empty':
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

    # @pyqtSlot(AttributeFormat)
    # def replace_line_edit(self, af: AttributeFormat):
    #     self.attributes_column.replace_line_edit(af)


class ObjectsTree(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)
        self.clean()

    def clean(self):
        self.class_nodes = set()
        if hasattr(self, 'tree_view'):
            self.tree_view.setParent(None)
        self.tree_view = QTreeView(self)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setExpandsOnDoubleClick(False)
        self.tree_model = QStandardItemModel()
        self.root_node = self.tree_model.invisibleRootItem()
        self.tree_view.setModel(self.tree_model)
        self.vbox.addWidget(self.tree_view)

    def init_from_graph_tree(self, tree_dict):
        self.clean()
        for class_name in tree_dict:
            item_class = QStandardItem(class_name)
            item_class.setEditable(False)
            item_class.setSelectable(False)
            self.root_node.appendRow(item_class)
            self.class_nodes.add(class_name)
            for obj_name in tree_dict[class_name]:
                item_obj = QStandardItem(obj_name)
                item_obj.setEditable(False)
                item_class.appendRow(item_obj)

        self.tree_view.expandAll()
        self.tree_view.doubleClicked.connect(self.get_value)

    def get_value(self, val):
        if val.data() not in self.class_nodes:
            print(val.data())


class ToolBarOfObjects(QToolBar):

    def __init__(self, min_size):
        super().__init__()
        self.setMinimumSize(min_size, min_size)
        self.wgt_main = QWidget(self)
        self.addWidget(self.wgt_main)

        self.title_label = QLabel('Tree of objects', self)
        self.title_label.setAlignment(Qt.AlignHCenter)

        self.objects_tree = ObjectsTree(self)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.title_label)
        self.vbox.addWidget(self.objects_tree)
        self.wgt_main.setLayout(self.vbox)

    @pyqtSlot(dict)
    def set_tree(self, tree_dict):
        self.objects_tree.init_from_graph_tree(tree_dict)


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
        self.ttb.extract_pictures(['CoordinateSystem', 'Point', 'Line', 'GroundLine'])
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
