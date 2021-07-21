from sm_globals_storage import SmGlobals as SmG


class NameObj:

    def __init__(self, name, obj):
        self.name = name
        self.obj = obj

    # def __eq__(self, other):
    #     return (self.name == other.name) and (self.obj == other.obj)
    #
    # def __hash__(self):
    #     return hash((self.name, self.obj))


class InstCounter:

    def __init__(self):
        self._count = 0
        self._insts = []

    def increaseCount(self):
        self._count += 1

    def resetCount(self):
        self._count = 0

    def addInst(self, inst):
        self._insts.append(NameObj(inst.Name, inst))
        self.increaseCount()

    def removeInst(self, inst, name_which_added=None):
        if name_which_added is None:
            name_which_added = inst.Name
        self._insts.remove(NameObj(name_which_added, inst))
        if not self.instSize:
            self.resetCount()

    @property
    def count(self):
        return self._count

    @property
    def insts(self):
        return self._insts

    @property
    def instSize(self):
        return len(self._insts)


class ObjsInspector:
    def __init__(self):
        self._insp_dict = {}

    def clsIsRegistered(self, cls):
        return cls in self._insp_dict.keys()

    def registerCls(self, cls):
        if not (self.clsIsRegistered(cls)):
            self._insp_dict[cls] = InstCounter()

    def registerObj(self, obj):
        cls_ierarh = reversed(obj.__class__.__mro__[:-1])
        for cls in cls_ierarh:
            if not self.clsIsRegistered(cls):
                self.registerCls(cls)
        self.removeObj(obj)
        self.addObj(obj)

    def getNumeration(self, cls):
        self.registerCls(cls)
        return self._insp_dict[cls].count + 1

    def getRegCell(self, obj):
        cls = obj.__class__
        res = list(filter(lambda x: x.obj == obj, self._insp_dict[cls].insts))
        if res:
            return res[0]

    def getInstances(self, cls):
        if not (self.clsIsRegistered(cls)):
            self.registerCls(cls)
        return [x.obj for x in self._insp_dict[cls].insts]  # {}

    def addObj(self, obj):
        cls_ierarh = obj.__class__.__mro__[:-1]
        for cls in cls_ierarh:
            self._insp_dict[cls].addInst(obj)
        SmG.add(obj.Name, obj)

    def removeObj(self, obj):
        cell_obj_registered = self.getRegCell(obj)
        if not (cell_obj_registered is None):
            cls_ierarh = reversed(obj.__class__.__mro__[:-1])
            for cls in cls_ierarh:
                self._insp_dict[cls].removeInst(obj, cell_obj_registered.name)
            SmG.pop(cell_obj_registered.name)

    def removeInstances(self, cls):
        for obj in self.getInstances(cls):
            self.removeObj(obj)

    def removeAllClassInstances(self):
        for cls in self._insp_dict.keys():
            for obj in self.getInstances(cls):
                self.removeObj(obj)

    def checkNameRepeating(self, cls, name_pretend):
        return any(map(lambda x: x.Name == name_pretend, self.getInstances(cls)))


Oi = ObjsInspector()
