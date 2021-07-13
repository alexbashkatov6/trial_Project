
import engine_core as ec
import sys
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QApplication, QToolBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt


class Example(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        textEdit = QTextEdit()
        self.setCentralWidget(textEdit)
        cs = ec.CoordinateSystem()
        print(cs.Name)
        #CoordinateSystem_1
        exitAction = QAction(QIcon('pictures/01_CS.jpg'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        qtb = QToolBar('Exit_1') #
        qtb.addAction(exitAction)
        self.addToolBar(Qt.LeftToolBarArea, qtb)
        #toolbar = self.addToolBar('') #'Exit_SuperExit'
        #toolbar = self.addToolBar(area=Qt.TopToolBarArea, toolbar=qtb) #LeftToolBarArea
        #toolbar.addAction(exitAction)

        self.setGeometry(300, 300, 350, 250)
        self.setWindowTitle('Main window')
        self.show()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


'''
import sys
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QApplication
from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtGui import QPainter, QPainterPath
from PyQt5.QtCore import pyqtSignal


class Drawer(QWidget):
    newPoint = pyqtSignal(QPoint)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.path = QPainterPath()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPath(self.path)

    def mousePressEvent(self, event):
        self.path.moveTo(event.pos())
        self.update()

    def mouseMoveEvent(self, event):
        self.path.lineTo(event.pos())
        self.newPoint.emit(event.pos())
        self.update()

    def sizeHint(self):
        return QSize(400, 400)


class MyWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setLayout(QVBoxLayout())
        label = QLabel(self)
        drawer = Drawer(self)
        drawer.newPoint.connect(lambda p: label.setText('Coordinates: ( %d : %d )' % (p.x(), p.y())))
        self.layout().addWidget(label)
        self.layout().addWidget(drawer)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MyWidget()
    w.show()
    sys.exit(app.exec_())
'''


'''
! Tree View Example
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView
from PyQt5.Qt import QStandardItemModel, QStandardItem
from PyQt5.QtGui import QFont, QColor


class StandardItem(QStandardItem):
    def __init__(self, txt='', font_size=12, set_bold=False, color=QColor(0, 0, 0)):
        super().__init__()

        fnt = QFont('Open Sans', font_size)
        fnt.setBold(set_bold)

        self.setEditable(False)
        self.setForeground(color)
        self.setFont(fnt)
        self.setText(txt)


class AppDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('World Country Diagram')
        self.resize(500, 700)

        treeView = QTreeView()
        treeView.setHeaderHidden(True)

        treeModel = QStandardItemModel()
        rootNode = treeModel.invisibleRootItem()


        # America
        america = StandardItem('America', 16, set_bold=True)

        california = StandardItem('California', 14)
        america.appendRow(california)

        oakland = StandardItem('Oakland', 12, color=QColor(155, 0, 0))
        sanfrancisco = StandardItem('San Francisco', 12, color=QColor(155, 0, 0))
        sanjose = StandardItem('San Jose', 12, color=QColor(155, 0, 0))

        california.appendRow(oakland)
        california.appendRow(sanfrancisco)
        california.appendRow(sanjose)


        texas = StandardItem('Texas', 14)
        america.appendRow(texas)

        austin = StandardItem('Austin', 12, color=QColor(155, 0, 0))
        houston = StandardItem('Houston', 12, color=QColor(155, 0, 0))
        dallas = StandardItem('dallas', 12, color=QColor(155, 0, 0))

        texas.appendRow(austin)
        texas.appendRow(houston)
        texas.appendRow(dallas)


        # Canada
        canada = StandardItem('America', 16, set_bold=True)

        alberta = StandardItem('Alberta', 14)
        bc = StandardItem('British Columbia', 14)
        ontario = StandardItem('Ontario', 14)
        canada.appendRows([alberta, bc, ontario])


        rootNode.appendRow(america)
        rootNode.appendRow(canada)

        treeView.setModel(treeModel)
        treeView.expandAll()
        treeView.doubleClicked.connect(self.getValue)

        self.setCentralWidget(treeView)

    def getValue(self, val):
        print(val.data())
        print(val.row())
        print(val.column())


app = QApplication(sys.argv)

demo = AppDemo()
demo.show()

sys.exit(app.exec_())
'''