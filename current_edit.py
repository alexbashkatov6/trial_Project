import sm_model_classes as smc

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class CurrentEdit(QObject):

    sendClassNameStr = pyqtSignal(str)
    sendAttribsStructure = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        self.extractedClasses = [i.__name__ for i in smc.BFP.allSubclasses()]
        self.activeClassName = self.extractedClasses[0]
        # print(self.activeClassName)
        self.attribsStructure = eval('smc.{}.attribs'.format(self.activeClassName))

    @pyqtSlot(str)
    def setClassName(self, val):
        self.activeClassName = val
        self.attribsStructure = eval('smc.{}.attribs'.format(self.activeClassName))
        self.sendClassNameStr.emit(val)
        self.sendAttribsStructure.emit(self.attribsStructure)


