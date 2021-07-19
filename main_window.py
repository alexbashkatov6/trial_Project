import current_edit as ce

import os
import re

from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QToolBar, QPushButton, QHBoxLayout, \
    QVBoxLayout, QLabel, QGridLayout, QWidget, QLayout, QLineEdit, QSplitter
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

class ToolBarOfAttribs(QToolBar):

    def __init__(self, min_size):
        super().__init__()
        self.activeClassLabel = QLabel('< pick tool >')
        self.activeClassLabel.setAlignment(Qt.AlignHCenter)
        wgtVertical = QWidget()
        self.setMinimumSize(min_size, min_size)
        vbox = QVBoxLayout()
        vbox.addWidget(self.activeClassLabel)
        wgtGrid = QWidget()
        self.attribsGrid = QGridLayout()
        for i in range(3):
            self.attribsGrid.addWidget(QLabel(str(i) + str(0)), i, 0, Qt.AlignHCenter)
            self.attribsGrid.addWidget(QLineEdit(str(i) + str(1)), i, 1, Qt.AlignHCenter)
        wgtGrid.setLayout(self.attribsGrid)
        vbox.addWidget(wgtGrid)
        wgtVertical.setLayout(vbox)
        self.addWidget(wgtVertical)

    @pyqtSlot(str)
    def setClassName(self, val):
        self.activeClassLabel.setText(val)

class MW(QMainWindow):

    def __init__(self):
        super().__init__()


        # widgets params
        left_toolbar_min_height_width = 50
        right_toolbar_min_height_width = 150

        # central wgt
        textEdit = QTextEdit()
        self.setCentralWidget(textEdit)

        # ce
        self.ce = ce.CurrentEdit()

        # Left tool bar format
        self.ltb = ToolBarOfClasses()
        self.ltb.extractPictures(self.ce.extractedClasses)
        self.ltb.constructWidget(left_toolbar_min_height_width)

        # Right tool bar format
        self.rtb = ToolBarOfAttribs(right_toolbar_min_height_width)

        self.addToolBar(Qt.LeftToolBarArea, self.ltb)
        self.addToolBar(Qt.RightToolBarArea, self.rtb)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        self.setGeometry(1000, 500, 550, 450)
        self.setWindowTitle('Main window')
        self.show()


# fileMenu.addAction(self._01_Action)
# csAction.setShortcut('Ctrl+Q')
# csAction.setStatusTip('Exit application')
# csAction.triggered.connect(self.close)

# sld.valueChanged.connect(lcd.display)
# closeApp = pyqtSignal()

# smc_classes_attribs = {class_name: {key: val for (key, val) in eval('smc.'+class_name).__dict__.items()
#                                     if not key.startswith('__')} for class_name in smc_classes_names}