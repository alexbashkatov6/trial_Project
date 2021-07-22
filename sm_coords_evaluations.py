from sm_enums import SmEnum, OneOf
import re


class CoordToBasisTransformation:
    def __init__(self, shift, direction):
        self.Shift = shift
        self.Direction = direction

    def __repr__(self):
        return '{}({},{})'.format(self.__class__.__name__, self.Shift, self.Direction)

    @property
    def Shift(self):
        return self._Shift

    @Shift.setter
    def Shift(self, value):
        assert isinstance(value, (int, float)), 'Expected type is int or float'
        self._Shift = value

    @property
    def Direction(self):
        return self._Direction

    @Direction.setter
    def Direction(self, value):
        assert abs(int(value)) == 1, 'Expected value is 1 or -1'
        self._Direction = value


class FieldCoord:
    def __init__(self, value, cs, axis=OneOf(SmEnum.FieldAxis, 'X')):
        self.Cs = cs
        self.Axis = axis
        self._X = None
        self._Y = None
        self.FloatCoord = value

    def __repr__(self):
        return '{}(({},{}),{})'.format(self.__class__.__name__, self._X, self._Y, self.Cs)

    @property
    def X(self):
        return self._X

    @X.setter
    def X(self, value):
        assert type(value) in [str, int, float], 'Expected type is str, int or float, given {}'.format(value)
        if type(value) in [int, float]:
            # self._X = CE.simpleSingleCast(value, float)
            pass
        else:
            assert bool(re.fullmatch(r'PK_\d+\+\d+', value)), 'Coord format is PK_xxxx+yyy, given {}'.format(value)
            plus_pos = value.find('+')
            self._X = float(int(value[3:plus_pos]) * 100 + int(value[plus_pos + 1:]))

    @property
    def Y(self):
        return self._Y

    @Y.setter
    def Y(self, value):

        # self._Y = CE.simpleSingleCast(value, float)
        pass

    @property
    def FloatCoord(self):
        return self._FloatCoord

    @FloatCoord.setter
    def FloatCoord(self, value):
        assert type(value) in [str, int, float, tuple], 'Expected type is tuple, str, int or float, given {}'.format(
            value)
        if not type(value) == tuple:
            if self.Axis.value == 'X':
                self.X = value
            else:
                self.Y = value
        else:
            assert len(value) == 2, 'Expected 2 coords: {}'.format(value)
            self.X = value[0]
            self.Y = value[1]
        self._FloatCoord = (self.X, self.Y)

    @property
    def PicketCoord(self):
        assert self.X.is_integer(), 'Cannot convert float {} to picket value'.format(self.X)
        # int_val = CE.simpleSingleCast(self.X, int)
        # return 'PK_{}+{}'.format(int_val // 100, int_val % 100)

    @property
    def Cs(self):
        return self._Cs

    @Cs.setter
    def Cs(self, value):
        # self._Cs = CE.simpleSingleCast(value, CoordinateSystem)
        pass

    @property
    def Axis(self):
        return self._Axis

    @Axis.setter
    def Axis(self, value):
        # self._Axis = CE.enumSimpleCast(value, E_FieldAxis)
        pass

    def __add__(self, other):
        assert type(other) in [int, float], 'Expected num. type of 2nd arg'
        return FieldCoord((self.X + other, self.Y), self.Cs)

    def __radd__(self, other):
        return self.add(other)

    # def __iadd__(self, other):
    #    return add(self, other)

    def __sub__(self, other):
        assert isinstance(other, FieldCoord) or (
                    type(other) in [int, float]), 'Expected type of 2nd arg - FieldCoord or num.'
        if type(other) in [int, float]:
            return FieldCoord((self.X - other, self.Y), self.Cs)
        else:
            assert self.Cs == other.Cs, 'Coords for sub need to be in same CS'
            return self.X - other.X

    def toBasis(self):
        basisCs = self.Cs.Basis.MainCoordSystem
        new_X = self.Cs.CoordToBasisTransformation.Shift + self.Cs.CoordToBasisTransformation.Direction * self.X
        return FieldCoord((new_X, self.Y), basisCs)
