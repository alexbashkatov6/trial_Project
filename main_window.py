import current_edit as ce
from sm_attrib_cell import ComplexAttrib, AttribGroup, CompetitorAttribGroup

import os
import re

from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QToolBar, QPushButton, QHBoxLayout, \
    QVBoxLayout, QLabel, QGridLayout, QWidget, QLayout, QLineEdit, QSplitter, QComboBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QRect


class ToolBarOfClasses(QToolBar):

    sendClassName = pyqtSignal(str)
    picFolder = 'pictures'

    def __init__(self):
        super().__init__()

    def extractPictures(self, classes_names):
        # pictures for tool icons extracting
        pic_names = {}
        nums_of_pict = []
        rootPath = os.getcwd()
        tree = os.walk(rootPath + '\\' + self.picFolder)
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

    def constructWidget(self, min_size):
        self.setMinimumSize(min_size, min_size)
        self.qb_list = []
        for pic_name in self.pic_names_sorted_list:
            icon = QIcon('{}/{}.jpg'.format(self.picFolder, pic_name))
            qb = QPushButton(icon, '')
            qb.setIconSize(QSize(min_size, min_size))
            qb.setToolTip(pic_name[pic_name.find('_') + 1:])
            qb.clicked.connect(self.actTriggered)
            self.qb_list.append(qb)
            self.addWidget(qb)

    def actTriggered(self):
        sender = self.sender()
        long_name = self.pic_names_sorted_list[self.qb_list.index(sender)]
        self.sendClassName.emit(long_name[long_name.index('_') + 1:])


class AttribRow(QHBoxLayout):
    def __init__(self, classMode=True):
        super().__init__()
        self.attrName = ''
        self.attrValue = ''
        self.labelWidget = QLabel(self.attrName)
        self.textEditWidget = QLineEdit(self.attrValue)
        self.addWidget(self.labelWidget)
        self.addWidget(self.textEditWidget)
        self.widgetsList = [self.labelWidget, self.textEditWidget]

        assert type(classMode) == bool, 'Bool is expected'
        if classMode:
            self.textEditWidget.setReadOnly(True)
            self.textEditWidget.setStyleSheet("background-color: grey")

    def setNameText(self, val):
        assert type(val) == str, 'Str is expected'
        self.labelWidget.setText(val)

    def setValueText(self, val):
        assert type(val) == str, 'Str is expected'
        self.textEditWidget.setText(val)


class ComboRow(QHBoxLayout):
    def __init__(self, classMode=True):
        super().__init__()
        self.comboName = ''
        self.labelWidget = QLabel(self.comboName)
        self.comboWidget = QComboBox()
        self.addWidget(self.labelWidget)
        self.addWidget(self.comboWidget)
        self.widgetsList = [self.labelWidget, self.comboWidget]

        assert type(classMode) == bool, 'Bool is expected'
        if classMode:
            self.comboWidget.setDisabled(True)

    def setComboName(self, val):
        assert type(val) == str, 'Str is expected'
        self.labelWidget.setText(val + ':')

    def addComboValue(self, val):
        assert type(val) == str, 'Str is expected'
        self.comboWidget.addItem(val)


class CreationButtonLayout(QHBoxLayout):
    def __init__(self, classMode=True):
        super().__init__()
        self.buttonWidget = QPushButton('Create/Apply')
        self.addWidget(self.buttonWidget)
        self.widgetsList = [self.buttonWidget]

        assert type(classMode) == bool, 'Bool is expected'
        if classMode:
            self.buttonWidget.setDisabled(True)


class AttribColumn(QVBoxLayout):
    def __init__(self):
        super().__init__()
        self.layoutList = []

    def addLayout(self, layout, stretch=0):
        self.layoutList.append(layout)
        super().addLayout(layout, stretch)

    def removeItem(self, a0):
        if type(a0) in [AttribRow, ComboRow, CreationButtonLayout]:
            for wgt in a0.widgetsList:
                wgt.hide()
        super().removeItem(a0)

    def initFromContainer(self, containerList, initEnter=True, classMode=True):
        assert type(containerList) == list, 'List is expected'
        assert all(map(lambda i: type(i) in [ComplexAttrib, CompetitorAttribGroup], containerList)), \
            'Expected attrib types'
        if initEnter:
            self.clean()
        for item in containerList:
            if type(item) == ComplexAttrib:
                new_row = AttribRow(classMode)
                self.addLayout(new_row)
                new_row.setNameText(item.name)
            if type(item) == CompetitorAttribGroup:
                new_row = ComboRow(classMode)
                self.addLayout(new_row)
                new_row.setComboName(item.name)
                group = item.attribGroups[0]
                new_row.addComboValue(group.name)
                self.initFromContainer(group.complexAttribs, False)
        if initEnter:
            crButL = CreationButtonLayout(classMode)
            self.addLayout(crButL)

    def clean(self):
        for layout in self.layoutList:
            self.removeItem(layout)
        self.layoutList.clear()


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

        # ce
        self.ce = ce.CurrentEdit()

        # Top tool bar format
        self.ttb = ToolBarOfClasses()
        self.ttb.extractPictures(self.ce.extractedClasses)
        self.ttb.constructWidget(top_toolbar_min_height_width)

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

        self.setGeometry(1000, 500, 550, 450)
        self.setWindowTitle('Main window')
        self.show()


