from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QToolBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt


class Example(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        textEdit = QTextEdit()
        self.setCentralWidget(textEdit)
        _01_Action = QAction(QIcon('pictures/01_CS.jpg'), 'Exit', self)
        _02_Action = QAction(QIcon('pictures/02_GroundLine.jpg'), 'Exit', self)
        _03_Action = QAction(QIcon('pictures/03_Point.jpg'), 'Exit', self)
        _04_Action = QAction(QIcon('pictures/04_Line.jpg'), 'Exit', self)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(_01_Action)

        qtb = QToolBar('Exit_1') #
        qtb.addAction(_01_Action)
        qtb.addAction(_02_Action)
        qtb.addAction(_03_Action)
        qtb.addAction(_04_Action)

        self.addToolBar(Qt.LeftToolBarArea, qtb)

        self.setGeometry(300, 300, 350, 250)
        self.setWindowTitle('Main window')
        self.show()

#csAction.setShortcut('Ctrl+Q')
#csAction.setStatusTip('Exit application')
#csAction.triggered.connect(self.close)