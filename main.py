from main_window import MW
from messages import MessagesManager
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject


class Director(QObject):
    def __init__(self):
        super().__init__()
        self.mw = MW()
        self.mm = MessagesManager(self.mw)
        self.setConnections()

    def setConnections(self):
        self.mw.actionTriggered.connect(self.mm.infoMessage)
        #self.mw.actionTriggered.connect(self.printValue)

    def printSender(self):
        ex_sender = self.mw.sender()
        print(ex_sender)

    def printValue(self, val):
        print(val)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = Director()
    sys.exit(app.exec_())


