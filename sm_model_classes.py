from sm_objs_inspector import Oi
import re


class BFP:

    def __init__(self, **kwargs):
        if 'Name' in kwargs.keys():
            name_pretend = kwargs['Name']
            prefix = self.__class__.__name__ + '_'
            assert not name_pretend[len(prefix):].isdigit(), 'Not auto-name cannot be (prefix + int); choose other name'
            self.Name = kwargs['Name']
        else:
            self.Name = '{}_{}'.format(self.__class__.__name__, Oi.getNumeration(self.__class__))
        Oi.registerObj(self)

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
        assert not Oi.checkNameRepeating(self.__class__, name_pretend), 'Name {} is already exists'.format(name_pretend)
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
                assert '_' + prop_name in self.__dict__.keys(), 'Prop {} not in obj'.format(prop_name)
                setattr(self, prop_name, getattr(self, '_' + prop_name))

    @classmethod
    def allSubclasses(cls):
        subclses = cls.__subclasses__()
        for subcls in subclses:
            subclses.extend(subcls.allSubclasses())
        return subclses


class CoordinateSystem(BFP):
    pass


class Point(BFP):
    pass


class Line(BFP):
    pass


class GroundLine(BFP):
    pass

pnt1, pnt2 = Point(), Point(Name='Point_tri')
print(pnt2.__dict__)
print(BFP.allSubclasses())
