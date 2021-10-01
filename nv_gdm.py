from __future__ import annotations
import re
from copy import copy

from nv_typing import *
from nv_bounded_string_set_class import BoundedStringSet


class GlobalDataManager:
    def __init__(self):
        self._name_to_obj: dict[str, Any] = {}
        self._obj_to_name: dict[Any, str] = {}  # for check obj repeating

    def register_obj_name(self, obj, name):
        assert name not in self.name_to_obj, 'Name repeating'
        assert obj not in self.obj_to_name, 'Obj repeating'
        assert not(obj is None), 'None value cannot be registered'
        self._name_to_obj[name] = obj
        self._obj_to_name[obj] = name

    def remove_obj_name(self, obj_or_name):
        obj, name = (self.name_to_obj[obj_or_name], obj_or_name) if type(obj_or_name) == str \
            else (obj_or_name, obj_or_name.name)
        self._name_to_obj.pop(name)
        self._obj_to_name.pop(obj)

    def check_name(self, name):
        return not(name in self.name_to_obj)

    @property
    def name_to_obj(self) -> dict[str, Any]:
        return copy(self._name_to_obj)

    @property
    def obj_to_name(self) -> dict[Any, str]:
        return copy(self._obj_to_name)


GDM = GlobalDataManager()


class NameDescriptor:

    def __init__(self, start_index=1):
        assert type(start_index) == int, 'Start index must be int'
        self.start_index = start_index

    def __get__(self, instance, owner=None):

        if not (instance is None) and not hasattr(instance, '_name'):
            instance._name = None

        if instance is None:
            return owner.__name__
        else:
            if not (instance._name is None):
                return instance._name
            else:
                raise ValueError('Name is not defined')

    def __set__(self, instance, name_candidate):
        if hasattr(instance, '_name'):
            GDM.remove_obj_name(instance)
        prefix = instance.__class__.__name__ + '_'
        if name_candidate == 'auto_name':
            i = self.start_index
            while True:
                if i < 1:
                    name_candidate = '{}{}'.format(prefix, '0'*(1-i))
                else:
                    name_candidate = '{}{}'.format(prefix, i)
                if GDM.check_name(name_candidate):
                    break
                else:
                    i += 1
        else:
            assert type(name_candidate) == str, 'Name need be str'
            assert bool(re.fullmatch(r'\w+', name_candidate)), 'Name have to consists of alphas, nums and _'
            assert name_candidate.startswith(prefix), 'Name have to begin from className_'
            assert name_candidate != prefix, 'name cannot be == prefix; add specification to end'
            assert not name_candidate[
                       len(prefix):].isdigit(), 'Not auto-name cannot be (prefix + int); choose other name'
            assert GDM.check_name(name_candidate), 'Name {} already exists'.format(name_candidate)
        instance._name = name_candidate
        GDM.register_obj_name(instance, name_candidate)


@strictly_typed
def str_to_obj(str_value: str, req_cls_str: str) -> tuple[Any, bool]:
    success = True

    if not str_value or str_value.isspace():
        return None, success

    req_cls = get_class_by_str(req_cls_str)

    if req_cls == str:
        return str_value, success

    if req_cls and issubclass(req_cls, BoundedStringSet):
        if str_value in req_cls.possible_strings:
            return req_cls(str_value), success
        else:
            return str_value, not success

    str_with_replaced_id = str_value
    found_identifier_candidates = re.findall(r'\w+', str_value)
    for fic in found_identifier_candidates:
        if fic in GDM.name_to_obj:
            str_with_replaced_id = str_with_replaced_id.replace(fic, 'GDM.name_to_obj["{}"]'.format(fic))
    try:
        obj = eval(str_with_replaced_id)
    except NameError:
        return str_value, not success
    else:
        if type_verification(req_cls_str, obj):
            return obj, success
        else:
            return str_value, not success


def obj_to_str(obj) -> str:

    if obj is None:
        return ''

    if type(obj) == type:
        return obj.__name__

    return str(obj)
