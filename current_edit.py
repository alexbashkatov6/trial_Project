import sm_model_classes as smc

from collections import OrderedDict

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class CurrentEdit(QObject):

    sendClassNameStr = pyqtSignal(str)
    # sendActiveAttribNameStr = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # smc extraction
        smc_classes_names = [i for i in dir(smc) if not i.startswith('__')]
        smc_classes_attribs = OrderedDict()
        for class_name in smc_classes_names:
            od = OrderedDict()
            for (key, val) in eval('smc.'+class_name).__dict__.items():
                if not key.startswith('__'):
                    od.update([(key, val)])
            smc_classes_attribs.update([(class_name, od)])
        self.extractedClasses = smc_classes_names
        self.extractedAttribs = smc_classes_attribs

        # active init
        self.activeClassName = smc_classes_names[0]
        self.activeAttribName = ''
        active_od = self.extractedAttribs[self.activeClassName]
        rand_elem_key = list(active_od.keys())[0]
        self.activeAttribName = rand_elem_key
        # self.refreshAttribs()
        # active_od = self.extractedAttribs[self.activeClassName]
        # rand_elem_key = list(active_od.keys())[0]
        # self.activeAttribName = rand_elem_key

    @pyqtSlot(str)
    def setClassName(self, val):
        self.activeClassName = val
        self.sendClassNameStr.emit(val)
        # self.refreshAttribs()

    # def refreshAttribs(self):
    #     active_od = self.extractedAttribs[self.activeClassName]
    #     rand_elem_key = list(active_od.keys())[0]
    #     self.activeAttribName = rand_elem_key
    #     # self.activeAttrib = (rand_elem_key, active_od[rand_elem_key])
    #     # print(self.activeAttrib)
    #
    # @pyqtSlot(str)
    # def setActiveAttribName(self, val):
    #     self.activeAttribName = val
    #     self.sendActiveAttribNameStr.emit(val)


