from sm_enums import SmEnum, OneOf


class TypedCell:
    def __init__(self, val=None, expType=None, intEqFloat=True):
        self.inValue = None
        self.value = None
        self.isIterable = False
        self.inExpectedType = None
        self.expectedType = None
        self.evalValueStatus = OneOf(SmEnum.EvalStatus, 'not_eval')
        self.evalTypeStatus = OneOf(SmEnum.EvalStatus, 'not_eval')
        assert type(intEqFloat) == bool, 'Expected bool type for intEqFloat'
        self.intEqFloat = intEqFloat

        assert (expType is None) or (type(expType) == str) or (type(expType) in [list, set]), \
            'Expected str type or None or list/set for exp-type, given {}'.format(expType)
        self.inExpectedType = expType
        if (expType is None) or (expType == 'str') or (type(expType) in [list, set]):
            self.expectedType = expType
            self.evalTypeStatus.value = 'eval_success'

        self.setValue(val)

    @staticmethod
    def strIsEmpty(val):
        if (type(val) == str) and ((not val) or val.isspace()):
            return True
        else:
            return False

    @staticmethod
    def convertNum(val, need_type):
        if not (need_type in [int, float]):
            return val
        else:
            if (type(val) == float) and (need_type == int) and not (val.is_integer()):
                raise ValueError('Cannot convert float {} to int'.format(val))
            return need_type(val)

    @staticmethod
    def checkIterableValue(val):
        if type(val) in [set, list]:
            return True
        return False

    def setValue(self, val):
        self.inValue = val
        self.evalValueStatus.value = 'not_eval'
        self.isIterable = False
        if self.expectedType == 'str':
            assert type(val) == str, 'Expected str type for in-value, given {}'.format(val)
            self.value = val
            self.evalValueStatus.value = 'eval_success'

    def checkExpectedType(self):
        if not (self.evalTypeStatus.value == 'eval_success'):
            self.expectedType = eval(self.inExpectedType)
            self.evalTypeStatus.value = 'eval_success'

    def checkValue(self):
        if not (self.evalTypeStatus.value == 'eval_success'):
            raise ValueError('Needed type is not evaluated yet')
        if not (self.evalValueStatus.value == 'eval_success'):
            if type(self.expectedType) in [list, set]:
                assert self.inValue in self.expectedType, 'Given value {} not in iterable {}' \
                    .format(self.inValue, self.expectedType)
                self.value = self.inValue
                self.evalValueStatus.value = 'eval_success'
                return
            if self.strIsEmpty(self.inValue) or (self.inValue is None):
                self.value = None
                self.evalValueStatus.value = 'eval_success'
                return
            if type(self.inValue) == str:
                try:
                    self.value = eval(self.inValue)
                except NameError:
                    self.evalValueStatus.value = 'eval_failed'
                    return
            else:
                self.value = self.inValue
            if self.checkIterableValue(self.value):
                self.isIterable = True
                return
            if self.intEqFloat:
                self.value = self.convertNum(self.value, self.expectedType)
            if not (self.expectedType is None):
                assert type(self.value) == self.expectedType, 'Type of given value {} not eq to needed {}' \
                    .format(self.value, self.expectedType)
            self.evalValueStatus.value = 'eval_success'


class ComplexAttrib:
    def __init__(self, name=None, val=None, expEachType=None):
        self.name = name
        self.candidateValue = val
        self.isCompulsory = True
        self.multiValue = False
        self.repeatableValue = False
        self.expectedTypeEachCell = expEachType
        self.evalStatusCommon = OneOf(SmEnum.EvalStatus, 'not_eval')
        self.cells = []  # TypedCell-s

    def setValue(self, val, clear=True):
        if clear:
            self.cells.clear()
        curr_status = True
        self.cells.append(TypedCell(val, self.expectedTypeEachCell))
        self.cells[-1].checkExpectedType()
        self.cells[-1].checkValue()
        if self.cells[-1].isIterable:
            curr_vals = self.cells[-1].value
            self.cells.pop()
            for single_val in curr_vals:
                curr_status *= self.setValue(single_val, False)
        return (self.cells[-1].evalTypeStatus.value == 'eval_success') and \
               (self.cells[-1].evalValueStatus.value == 'eval_success')


class AttribGroup:
    def __init__(self):
        self.name = None
        self.attribs = None
        self.mainAttr = None
        self.isActive = None


class CompetitorAttribGroup:
    def __init__(self):
        self.name = None
        self.attribGroups = []

    # def activate(self):
    #     pass
    #
    # def deactivate(self):
    #     pass

    # def addMethod(self, methodName, attrGroup):
    #     self.methods[methodName] = attrGroup
