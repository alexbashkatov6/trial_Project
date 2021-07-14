class CellEval:
    def __init__(self):
        self.candidateValue = None
        self.value = None
        self.evalStatus = False
        self.expectedType = None


class ComplexAttrib:
    def __init__(self):
        self.name = None
        self.isCompulsory = False
        self.cell = CellEval()
        self.expectedType = None
        self.isIterable = False
        self.isRepeatable = False


class AttribsGroup:
    def __init__(self):
        self.mainAttr = None
        self.attribs = None
        self.isActive = None

    def activate(self):
        pass

    def deactivate(self):
        pass


class CreationMethodsGroup:
    def __init__(self):
        self.mainMethod = None
        self.activeMethod = None
        self.methods = {}

    def addMethod(self, methodName, attrGroup):
        self.methods[methodName] = attrGroup



