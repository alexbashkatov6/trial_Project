from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QToolBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal


class MW(QMainWindow):

    actionTriggered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        #self.

        textEdit = QTextEdit()
        self.setCentralWidget(textEdit)
        picFolder = 'pictures'
        self.pic_names = ['01_CS', '02_GroundLine', '03_Point', '04_Line']
        self.actions_ = [QAction(QIcon('{}/{}.jpg'.format(picFolder, pic_name)), 'Exit', self)
                         for pic_name in self.pic_names]
        # self.actions_[0].triggered.connect()
        list(map(lambda x: x.triggered.connect(self.actTriggered), self.actions_))

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')


        qtb = QToolBar('Exit_1')
        qtb.addActions(self.actions_)

        self.addToolBar(Qt.LeftToolBarArea, qtb)

        self.setGeometry(1000, 500, 550, 450)
        self.setWindowTitle('Main window')
        self.show()

    def actTriggered(self):
        sender = self.sender()
        self.actionTriggered.emit(self.pic_names[self.actions_.index(sender)]) #print(self.actions_.index(sender))

# fileMenu.addAction(self._01_Action)
# csAction.setShortcut('Ctrl+Q')
# csAction.setStatusTip('Exit application')
# csAction.triggered.connect(self.close)

# sld.valueChanged.connect(lcd.display)
# closeApp = pyqtSignal()