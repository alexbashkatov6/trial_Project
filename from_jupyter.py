import pandas as pd
import os
import re

# ENUMS def
class rEnum:
    def __init__(self, name, *str_values):
        assert type(name) == str, 'Name need be str type'
        assert bool(re.fullmatch(r'\w+', name)), 'Name have to consists of alphas, nums and _'
        assert not name[0].isdigit(), 'Name cannot begins from digit'
        assert all(map(lambda i: type(i) == str, str_values)), 'Keys need be str type'
        assert len(set(str_values)) == len(str_values), 'Enum need have unique keys'
        for str_val in str_values:
            self.__dict__[str_val] = '{}.{}'.format(name,str_val)
        globals()[name] = self
    
    @property
    def possibleValues(self):
        return [eval(i) for i in self.__dict__.values()]

rEnum ('E_MergePolicy','Direct', \
                       'Side')

rEnum ('E_FieldAxis','X', \
                     'Y')

rEnum ('E_SigColor','R', \
                    'B', \
                    'W', \
                    'Y', \
                    'G')

rEnum ('E_SigType','Train', \
                   'Man', \
                   'AB', \
                   'NeighbourStationInTrain', \
                   'Repeat', \
                   'Warning')

rEnum ('E_Direct','Plus', \
                  'Minus')

rEnum ('E_IsolSegmType','STREL', \
                        'BESSTREL', \
                        'STREL_ON_STRVP', \
                        'BESSTREL_ON_STRVP', \
                        'PUT', \
                        'INDIC', \
                        'ABTC', \
                        'PABRC', \
                        'FICTIVE')

rEnum ('E_RefreshData','ALL', \
                       'NEW_CS', \
                       'NEW_POINT', \
                       'NEW_LINE', \
                       'NEW_SEGMENT')


class Defaults:

    def __init__(self):
        self.InterRailDist = 5.3


DFLT = Defaults()


class CastEvaluations:

    def inputIsStr(self, in_value):
        return type(in_value) == str

    def intToFloat(self, in_value, need_type):
        if (need_type == float) and (type(in_value) == int):
            return float(in_value)
        else:
            return in_value

    def floatToInt(self, in_value, need_type):
        if (need_type == int) and (type(in_value) == float):
            assert in_value.is_integer(), 'Expected integer str_value, given is {}'.format(in_value)
            return int(in_value)
        else:
            return in_value

    def floatIntEquivalence(self, in_value, need_type):
        in_value = self.intToFloat(in_value, need_type)
        in_value = self.floatToInt(in_value, need_type)
        return in_value

    def emptyStrAsNone(self, in_value):
        if (type(in_value) == str) and (in_value.isspace() or not in_value):
            return None
        else:
            return in_value

    def autoCast(self, in_value):
        in_value = self.emptyStrAsNone(in_value)
        if not in_value is None:
            if self.inputIsStr(in_value):
                return eval(in_value)
            else:
                return in_value
        else:
            return in_value

    def strCast(self, in_value):
        in_value = self.emptyStrAsNone(in_value)
        if not in_value is None:
            assert self.inputIsStr(in_value), 'Input type is not a str : {}'.format(in_value)
        return in_value

    def simpleSingleCast(self, in_value, need_type, floatIntEquiv=True):  # int, float, bool, simple class
        in_value = self.emptyStrAsNone(in_value)
        if not in_value is None:
            if self.inputIsStr(in_value):
                out_value = eval(in_value)
            else:
                out_value = in_value
            if floatIntEquiv:
                out_value = self.floatIntEquivalence(out_value, need_type)
            assert issubclass(type(out_value), need_type), 'Cannot convert to {} : {}'.format(need_type.__name__,
                                                                                              out_value)
            return out_value
        else:
            return in_value

    def simpleIterableCast(self, in_value, need_iterable_type, need_each_type, need_count=None, floatIntEquiv=True):
        assert need_iterable_type in [set, list, tuple], 'Type iterable {} is not supported'.format(need_iterable_type)
        in_value = self.emptyStrAsNone(in_value)
        if not in_value is None:
            if self.inputIsStr(in_value):
                out_value = eval(in_value)
            else:
                out_value = in_value
            assert type(out_value) == need_iterable_type, 'Need type of iterable is {}'.format(need_iterable_type)
            if floatIntEquiv:
                out_value = need_iterable_type([self.floatIntEquivalence(i, need_each_type) for i in out_value])
            assert all(map(lambda i: issubclass(type(i), need_each_type),
                           out_value)), 'Not all elements of class {} : {}'.format(need_each_type.__name__, out_value)
            if not need_count is None:
                assert type(need_count) == int, 'Need_count need to be int, given str_value is {}'.format(need_count)
                assert len(out_value) == need_count, 'Needed count is {}, given str_value is {}'.format(need_count,
                                                                                                    out_value)
            return out_value
        else:
            return in_value

    def customCast(self, in_value, func_cast_success):
        in_value = self.emptyStrAsNone(in_value)
        if not in_value is None:
            if self.inputIsStr(in_value):
                out_value = eval(in_value)
            else:
                out_value = in_value
            assert func_cast_success(out_value), 'Convert result not satisfy func_cast_success : {}'.format(out_value)
            return out_value
        else:
            return in_value

    def enumSimpleCast(self, in_value, enum_of_value):
        in_value = self.emptyStrAsNone(in_value)
        if not in_value is None:
            if self.inputIsStr(in_value):
                out_value = eval(in_value)
            else:
                out_value = in_value
            assert out_value in enum_of_value.possibleValues, 'Value {} not in possb. base_enum vals. {}'.format(out_value,
                                                                                                            enum_of_value.possibleValues)
            return out_value
        else:
            return in_value

    def enumIterableCast(self, in_value, need_iterable_type, enum_of_each_value, need_count=None):
        assert need_iterable_type in [set, list, tuple], 'Type iterable {} is not supported'.format(need_iterable_type)
        in_value = self.emptyStrAsNone(in_value)
        if not in_value is None:
            if self.inputIsStr(in_value):
                out_value = eval(in_value)
            else:
                out_value = in_value
            assert type(out_value) == need_iterable_type, 'Need type of iterable is {}'.format(need_iterable_type)
            assert all(map(lambda i: i in enum_of_each_value.possibleValues,
                           out_value)), 'Not all elements is base_enum vals {} : {}'.format(enum_of_each_value,
                                                                                       out_value)
            if not need_count is None:
                assert type(need_count) == int, 'Need_count need to be int, given str_value is {}'.format(need_count)
                assert len(out_value) == need_count, 'Needed count is {}, given str_value is {}'.format(need_count,
                                                                                                    out_value)
            return out_value
        else:
            return in_value


CE = CastEvaluations()

class NameObj:

    def __init__(self, name, obj):
        self.name = name
        self.obj = obj

    def __eq__(self, other):
        return (self.name == other.name) and (self.obj == other.obj)

    def __hash__(self):
        return hash((self.name, self.obj))


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
        if not (self.instSize):
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


# if 'OI' in globals():
#    OI.removeAllClassInstances()

class ObjsInspector:

    def __init__(self):
        self._insp_dict = {}

    def clsIsRegistered(self, cls):
        return (cls in self._insp_dict.keys())

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
        return (self._insp_dict[cls].count + 1)

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
        globals()[obj.Name] = obj

    def removeObj(self, obj):
        cell_obj_registered = self.getRegCell(obj)
        if not (cell_obj_registered is None):
            cls_ierarh = reversed(obj.__class__.__mro__[:-1])
            for cls in cls_ierarh:
                self._insp_dict[cls].removeInst(obj, cell_obj_registered.name)
            globals().pop(cell_obj_registered.name)

    def removeInstances(self, cls):
        for obj in self.getInstances(cls):
            self.removeObj(obj)

    def removeAllClassInstances(self):
        for cls in self._insp_dict.keys():
            for obj in self.getInstances(cls):
                self.removeObj(obj)

    def checkNameRepeating(self, cls, name_pretend):
        return any(map(lambda x: x.Name == name_pretend, self.getInstances(cls)))


OI = ObjsInspector()

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
        assert abs(int(value)) == 1, 'Expected str_value is 1 or -1'
        self._Direction = value
        
class FieldCoord:
    def __init__(self, value, cs, axis = E_FieldAxis.X):
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
        assert type(value) in [str,int,float], 'Expected type is str, int or float, given {}'.format(value)
        if type(value) in [int,float]:
            self._X = CE.simpleSingleCast(value, float)
        else:
            assert bool(re.fullmatch(r'PK_\d+\+\d+', value)), 'Coord format is PK_xxxx+yyy, given {}'.format(value)
            plus_pos = value.find('+')
            self._X = float(int(value[3:plus_pos]) * 100 + int(value[plus_pos + 1:]))
    
    @property
    def Y(self):
        return self._Y
    @Y.setter
    def Y(self, value):
        self._Y = CE.simpleSingleCast(value, float)
        
    @property
    def FloatCoord(self):
        return self._FloatCoord
    @FloatCoord.setter
    def FloatCoord(self, value):
        assert type(value) in [str,int,float,tuple], 'Expected type is tuple, str, int or float, given {}'.format(value)
        if not type(value) == tuple:
            if self.Axis == E_FieldAxis.X:
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
        assert self.X.is_integer(), 'Cannot convert float {} to picket str_value'.format(self.X)
        int_val = CE.simpleSingleCast(self.X, int)
        return 'PK_{}+{}'.format(int_val//100, int_val%100)
        
    @property
    def Cs(self):
        return self._Cs
    @Cs.setter
    def Cs(self, value):
        self._Cs = CE.simpleSingleCast(value, CoordinateSystem)
    
    @property
    def Axis(self):
        return self._Axis
    @Axis.setter
    def Axis(self, value):
        self._Axis = CE.enumSimpleCast(value, E_FieldAxis)
        
    def __add__(self, other):
        assert type(other) in [int, float], 'Expected num. type of 2nd arg'
        return FieldCoord((self.X + other, self.Y), self.Cs)
    
    def __radd__(self, other):
        return add(self, other)
    
    #def __iadd__(self, other):
    #    return add(self, other)
    
    def __sub__(self, other):
        assert isinstance(other, FieldCoord) or (type(other) in [int, float]), 'Expected type of 2nd arg - FieldCoord or num.'
        if type(other) in [int, float]:
            return FieldCoord((self.X - other, self.Y), self.Cs)
        else:
            assert self.Cs == other.Cs , 'Coords for sub need to be in same CS'
            return self.X - other.X 
        
    def toBasis(self):
        basisCs = self.Cs.Basis.MainCoordSystem
        new_X = self.Cs.CoordToBasisTransformation.Shift + self.Cs.CoordToBasisTransformation.Direction * self.X
        return FieldCoord((new_X, self.Y), basisCs)
        


class BFP():
    
    def __init__(self,**kwargs):
        if 'Name' in kwargs.keys():
            name_pretend = kwargs['Name']
            prefix = self.__class__.__name__ + '_'
            assert not name_pretend[len(prefix):].isdigit(), 'Not auto-name cannot be (prefix + int); choose other name'
            self.Name = kwargs['Name']
        else:
            self.Name = '{}_{}'.format(self.__class__.__name__, OI.getNumeration(self.__class__))
        OI.registerObj(self)
        
    def __repr__(self):
        return self._Name
        
    @property
    def Name(self):
        return self._Name
    
    @Name.setter
    def Name(self, name_pretend):
        prefix = self.__class__.__name__ + '_'
        assert type(name_pretend) == str, 'Name need be str'
        assert bool(re.fullmatch(r'\w+', name_pretend)), 'Name have to consists of alphas, nums and _'
        assert name_pretend.startswith(prefix), 'Name have to begin from className_'
        assert not OI.checkNameRepeating(self.__class__, name_pretend), 'Name {} is already exists'.format(name_pretend)
        self._Name = name_pretend
        
    def strInitialization(self, new_attribs_dict):
        curr_attribs_dict = self.__dict__
        for attr_name, attr_new_value in new_attribs_dict.items():
            if attr_name == 'Name':
                continue
            assert ('_' + attr_name) in curr_attribs_dict.keys(), 'Attrib {} not found'.format(attr_name)
            if type(attr_new_value) == str:
                setattr(self, '_' + attr_name, attr_new_value)
            else:
                setattr(self, attr_name, attr_new_value)
            
    def strEvaluation(self):
        # automatically works only for properties... thats enough ?
        cls_ierarh = reversed(self.__class__.__mro__[:-1])
        for cls in cls_ierarh:
            cls_prop_names = list(filter(lambda i: type(cls.__dict__[i]) == property, cls.__dict__.keys()))
            for prop_name in cls_prop_names:
                if prop_name == 'Name':
                    continue
                assert '_' + prop_name in self.__dict__.keys() , 'Prop {} not in obj'.format(prop_name)
                setattr(self, prop_name, getattr(self, '_' + prop_name))
    
    @classmethod
    def allSubclasses(cls):
        subclses = cls.__subclasses__()
        for subcls in subclses:
            subclses.extend(subcls.allSubclasses())
        return subclses

class BasisLine:
    pass

class Basis(BFP):
    File = 'BASIS'
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._MainCoordSystem = None
        self._CoordSystems = []
        self._BasisLines = []
        
        self.strInitialization(kwargs)
        
    @property
    def MainCoordSystem(self):
        return self._MainCoordSystem
    @MainCoordSystem.setter
    def MainCoordSystem(self, value):
        self._MainCoordSystem = CE.simpleSingleCast(value, CoordinateSystem)
        
    @property
    def CoordSystems(self):
        return self._CoordSystems
    @CoordSystems.setter
    def CoordSystems(self, value):
        self._CoordSystems = CE.simpleIterableCast(value, list, CoordinateSystem)
        
    @property
    def BasisLines(self):
        return self._BasisLines
    @BasisLines.setter
    def BasisLines(self, value):
        self._BasisLines = CE.simpleIterableCast(value, list, BasisLine)
        
    def addCoordSystem(self, value):
        self._CoordSystems.append(CE.simpleSingleCast(value, CoordinateSystem))
        
    def removeCoordSystem(self, value):
        self._CoordSystems.remove(value)
        
    def addBasisLine(self, value):
        self._BasisLines.append(CE.simpleSingleCast(value, BasisLine))
        
    def removeBasisLine(self, value):
        self._BasisLines.remove(value)

class CoordinateSystem(BFP):
    File = 'COORD_SYSTEMS'
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._FieldCoord = None
        self._RelCsCoDirect = None
        self._CoordToBasisTransformation = None 
        self._Basis = None
        
        self.strInitialization(kwargs)
        
    @property
    def FieldCoord(self):
        return self._FieldCoord
    @FieldCoord.setter
    def FieldCoord(self, value):
        self._FieldCoord = CE.simpleSingleCast(value, FieldCoord)
        
    @property
    def RelCsCoDirect(self):
        return self._RelCsCoDirect
    def RelCsCoDirectChecker(self, value):
        return abs(int(value)) == 1
    @RelCsCoDirect.setter
    def RelCsCoDirect(self, value):
        self._RelCsCoDirect = CE.customCast(value, self.RelCsCoDirectChecker)
        
    @property
    def CoordToBasisTransformation(self):
        return self._CoordToBasisTransformation
    @CoordToBasisTransformation.setter
    def CoordToBasisTransformation(self, value):
        self._CoordToBasisTransformation = CE.simpleSingleCast(value, CoordToBasisTransformation)
        
    @property
    def Basis(self):
        return self._Basis
    @Basis.setter
    def Basis(self, value):
        self._Basis = CE.simpleSingleCast(value, Basis)
           
    def basisEvaluations(self, main_in_basis = False):
        if main_in_basis:
            self.Basis = main_in_basis
            self.CoordToBasisTransformation = CoordToBasisTransformation(0,1)
        else:
            relCsSystemCBT = self.FieldCoord.Cs.CoordToBasisTransformation
            self.Basis = self.FieldCoord.Cs.Basis
            self.CoordToBasisTransformation = CoordToBasisTransformation(relCsSystemCBT.Shift + self.FieldCoord.X,\
                                                                     relCsSystemCBT.Direction * self.RelCsCoDirect)
      
class Point(BFP):
    File = 'BASEPOINTS'
    def __init__(self,**kwargs): 
        super().__init__(**kwargs)
        self._OnPoint = None # Point
        self._FieldCoord = None
        self._Line = None # Line
        
        self.strInitialization(kwargs)
        
    @property
    def OnPoint(self):
        return self._OnPoint
    @OnPoint.setter
    def OnPoint(self, value):
        self._OnPoint = CE.simpleSingleCast(value, Point)
        
    @property
    def FieldCoord(self):
        return self._FieldCoord
    @FieldCoord.setter
    def FieldCoord(self, value):
        self._FieldCoord = CE.simpleSingleCast(value, FieldCoord)

class Line(BFP):
    File = 'BASELINES'
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._Point_Begin = None 
        self._Point_End = None
        self._Angle = None # int ?
        self._Order = None # int 
        self._PointsList = None 
        self._cElemsSet = set() 
        
        self.strInitialization(kwargs)
        
class Light(BFP):
    File = 'LIGHTS'
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._PlacePoint = None
        self._StartRoutePoints = None  # list
        self._Type = None
        self._Direction = None
        self._Colors = None  # list
        self._MainSignal = None
        
        self.strInitialization(kwargs)
        
class Pipeline:
    
    def resetOI(self):
        OI.removeAllClassInstances()
        
    def initObjsFromFiles(self):
        rootPath = os.getcwd()
        
        classes = BFP.allSubclasses()
        for cls in classes:
            tree = os.walk(rootPath)
            if 'File' in cls.__dict__.keys():
                assert type(cls.File) == str, 'File name need be str'
                for d, dirs, files in tree:
                    for file in files:
                        if len(file)>3 and file[-4:]=='.csv':
                            file_short_name = file[:-4]
                            file_fullPath = d + '\\' + file
                            if file_short_name == cls.File:
                                df = pd.read_csv(file_fullPath, sep=';', dtype='str', keep_default_na=False)
                                for index in df.index:
                                    attribsDict = {}
                                    for column in df.columns:
                                        if column=='Npp':
                                            continue
                                        attribsDict[column] = df.loc[index,column]
                                    cls(**attribsDict)
    
    def evaluateObjAttribs(self):
        classes = BFP.allSubclasses()
        for cls in classes:
            objs = OI.getInstances(cls)
            for obj in objs:
                obj.strEvaluation()
                
    def evaluateBases(self):
        bases = OI.getInstances(Basis)
        main_css = dict({(basis.MainCoordSystem, basis) for basis in bases})
        css = OI.getInstances(CoordinateSystem)
        for cs in css:
            if cs in main_css.keys():
                cs.basisEvaluations(main_css[cs])
            else:
                cs.basisEvaluations()
   
    def writeDataFile(self, cls, file_name, folder):
        rootPath = os.getcwd()
        if not (folder in os.listdir(path = rootPath)):
            os.mkdir(rootPath + '\\' + folder)
        currDir = rootPath + '\\' + folder
            
        columns = ['Npp'] 
        cls_ierarh = reversed(cls.__mro__[:-1])
        for cls1 in cls_ierarh:
            cls_prop_names = list(filter(lambda i: type(cls1.__dict__[i]) == property, cls1.__dict__.keys()))
            for prop_name in cls_prop_names:
                columns.append(prop_name)
                
        Npp = 0
        rows = []
        objs = OI.getInstances(cls)
        for obj in objs:
            for column in columns:
                if column == 'Npp':
                    Npp += 1
                    new_row = [str(Npp)]
                else:
                    attr_val = getattr(obj, column)
                    if not attr_val is None:
                        attr_val = str(attr_val)
                    new_row.append(attr_val)
            rows.append(new_row)
        df = pd.DataFrame(rows, columns=columns) 
        df.to_csv('{}\\{}.csv'.format(currDir, file_name), sep = ';', index=False)
