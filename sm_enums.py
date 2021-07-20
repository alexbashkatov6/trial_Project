class SmEnum:
    EvalStatus = {'not_eval', 'eval_success', 'eval_failed'}


class OneOf:
    def __init__(self, values, choice=None):
        assert type(values) in [list, set], 'Values need be list or set, given {}'.format(type(values))
        self.availableValues = values
        self._value = choice

    def __repr__(self):
        return self._value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if val is None:
            self._value = val
            return
        assert val in self.availableValues, 'Values need be from available: {}'.format(self.availableValues)
        self._value = val

