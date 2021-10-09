import os
import re

from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QToolBar, QPushButton, QHBoxLayout, \
    QVBoxLayout, QLabel, QGridLayout, QWidget, QLayout, QLineEdit, QSplitter, QComboBox
from PyQt5.QtGui import QIcon, QPainter, QPen
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QRect, QPoint


class ToolBarOfClasses(QToolBar):

    sendClassName = pyqtSignal(str)
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
        self.sendClassName.emit(long_name[long_name.index('_') + 1:])


class AttribColumn(QVBoxLayout):

    def clean(self):
        for layout in self.children():
            index = layout.count()
            while index > 0:
                my_widget = layout.itemAt(index-1).widget()
                my_widget.setParent(None)
                index -= 1

    def init_from_container(self, af_list):
        self.clean()
        for af in af_list:
            attr_layout = QHBoxLayout()
            if af.attr_type == 'title':
                attr_layout.addWidget(QLabel(af.attr_name))
            if af.attr_type == 'splitter':
                attr_layout.addWidget(QLabel(af.attr_name))
                cb = QComboBox()
                cb.addItems(af.possible_values)
                cb.setCurrentText(af.attr_value)
                attr_layout.addWidget(cb)
            if af.attr_type == 'value':
                attr_layout.addWidget(QLabel(af.attr_name))
                attr_layout.addWidget(QLineEdit(af.attr_value))
            self.addLayout(attr_layout)

# QPushButton('Create/Apply')


class ToolBarOfAttribs(QToolBar):

    def __init__(self, min_size):
        super().__init__()
        self.activeClassLabel = QLabel('< pick tool >')
        self.activeClassLabel.setAlignment(Qt.AlignHCenter)
        self.wgtVertical = QWidget()
        self.setMinimumSize(min_size, min_size)
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.activeClassLabel)
        self.wgtGrid = QWidget()
        self.attribsColumn = AttribColumn()
        self.wgtGrid.setLayout(self.attribsColumn)
        self.vbox.addWidget(self.wgtGrid)
        self.wgtVertical.setLayout(self.vbox)
        self.addWidget(self.wgtVertical)

    @pyqtSlot(str)
    def setClassName(self, val):
        self.activeClassLabel.setText(val)

    @pyqtSlot(list)
    def setAttrStruct(self, val):
        self.attribsColumn.initFromContainer(val)

    @pyqtSlot(list)
    def set_attr_struct(self, af_list):
        self.attribsColumn.init_from_container(af_list)


class ToolBarOfObjects(QToolBar):

    def __init__(self, min_size):
        super().__init__()
        self.setMinimumSize(min_size, min_size)


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
        self.rtb = ToolBarOfAttribs(right_toolbar_min_height_width)

        # Left tool bar format
        self.ltb = ToolBarOfObjects(left_toolbar_min_height_width)

        self.addToolBar(Qt.TopToolBarArea, self.ttb)
        self.addToolBar(Qt.RightToolBarArea, self.rtb)
        self.addToolBar(Qt.LeftToolBarArea, self.ltb)


        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

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
        
    # def cl
