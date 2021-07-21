from sm_enums import SmEnum, OneOf


class TypedCell:
    def __init__(self, val=None, expType=None, intEqFloat=True):
        self.inValue = None
        self.value = None
        self.isIterable = False
        self.expectedType = expType
        self.evalValueStatus = OneOf(SmEnum.EvalStatus, 'not_eval')
        assert type(intEqFloat) == bool, 'Expected bool type for intEqFloat'
        self.intEqFloat = intEqFloat

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

    def checkValue(self):
        if not (self.evalValueStatus.value == 'eval_success'):
            if self.strIsEmpty(self.inValue) or (self.inValue is None):
                self.value = None
                self.evalValueStatus.value = 'eval_success'
                return
            if (type(self.inValue) == str) and \
                    not ((type(self.expectedType) in [list, set]) and (self.inValue in self.expectedType)):
                try:
                    self.value = eval(self.inValue)
                except NameError:
                    self.evalValueStatus.value = 'eval_failed'
                    return
            else:
                self.value = self.inValue
            if self.checkIterableValue(self.value):
                self.isIterable = True
                self.evalValueStatus.value = 'eval_success'
                return
            if type(self.expectedType) in [list, set]:
                assert self.value in self.expectedType, 'Given value {} not in iterable {}' \
                    .format(self.value, self.expectedType)
                self.evalValueStatus.value = 'eval_success'
                return
            if self.intEqFloat:
                self.value = self.convertNum(self.value, self.expectedType)
            if not (self.expectedType is None):
                assert type(self.value) == self.expectedType, 'Type of given value {} not eq to needed {}' \
                    .format(self.value, self.expectedType)
            self.evalValueStatus.value = 'eval_success'


class ComplexAttrib:
    def __init__(self, name=None, expEachType=None, multi=False):  # , val=None
        self.name = name
        assert type(multi) == bool, 'Expected multi is bool'
        self.multiValue = multi
        self.isCompulsory = True
        self.repeatableValue = True

        self.inExpectedTypeEachCell = None
        self.expectedTypeEachCell = None
        self.evalTypeStatus = OneOf(SmEnum.EvalStatus, 'not_eval')

        self.evalStatusCommonCells = OneOf(SmEnum.EvalStatus, 'not_eval')
        self.cells = []

        assert (expEachType is None) or (type(expEachType) == str) or (type(expEachType) in [list, set]), \
            'Expected str type or None or list/set for exp-type, given {}'.format(expEachType)
        self.inExpectedTypeEachCell = expEachType
        if (expEachType is None) or (expEachType == 'str') or (type(expEachType) in [list, set]):
            self.expectedTypeEachCell = expEachType
            self.evalTypeStatus.value = 'eval_success'

    def checkExpectedType(self):
        if not (self.evalTypeStatus.value == 'eval_success'):
            self.expectedTypeEachCell = eval(self.inExpectedTypeEachCell)
            self.evalTypeStatus.value = 'eval_success'

    def setValue(self, val):
        assert self.evalTypeStatus.value == 'eval_success', 'Cannot set value if expected type is not defined'
        self.evalStatusCommonCells.value = 'not_eval'
        self.cells.clear()
        self.cells.append(TypedCell(val, self.expectedTypeEachCell))

    def checkValue(self):
        assert self.cells, 'No values in cells'
        self.cells[-1].checkValue()
        curr_status = (self.cells[-1].evalValueStatus.value == 'eval_success')
        if self.cells[-1].isIterable:
            assert self.multiValue, 'Expected single value'
            curr_vals = self.cells[-1].value
            self.cells.pop()
            for single_val in curr_vals:
                self.cells.append(TypedCell(single_val, self.expectedTypeEachCell))
                curr_status *= self.checkValue()
        self.evalStatusCommonCells.value = 'eval_success' if curr_status else 'eval_failed'
        return self.cells[-1].evalValueStatus.value == 'eval_success'


class AttribGroup:
    def __init__(self, name=None, complexAttribs=None, mainAttrName=None, isActive=False):
        if complexAttribs is None:
            complexAttribs = []
        self.name = name
        self.complexAttribs = complexAttribs
        self.mainAttrName = mainAttrName
        self.isActive = isActive


class CompetitorAttribGroup:
    def __init__(self, name=None, attribGroups=None):
        if attribGroups is None:
            attribGroups = []
        self.name = name
        self.attribGroups = attribGroups

