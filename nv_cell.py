from __future__ import annotations
import re
from copy import copy
from functools import partial

from nv_typing import *
from nv_bounded_string_set_class import BoundedStringSet  # bounded_string_set,


class CellError(Exception):
    pass


class TypeCellError(CellError):
    pass


class SyntaxCellError(CellError):
    pass


class SemanticCellError(CellError):
    pass


class GlobalNamesManager:
    def __init__(self):
        self._name_to_obj: dict[str, Any] = {}
        self._obj_to_name: dict[Any, str] = {}  # for check obj repeating

    def register_obj_name(self, obj, name):
        if type(obj) == str:
            obj, name = name, obj
        assert name not in self.name_to_obj, 'Name repeating'
        assert obj not in self.obj_to_name, 'Obj repeating'
        assert not (obj is None), 'None value cannot be registered'
        self._name_to_obj[name] = obj
        self._obj_to_name[obj] = name

    def remove_obj_name(self, obj_or_name):
        obj, name = (self.name_to_obj[obj_or_name], obj_or_name) if type(obj_or_name) == str \
            else (obj_or_name, self.obj_to_name[obj_or_name])
        self._name_to_obj.pop(name)
        self._obj_to_name.pop(obj)

    def check_new_name(self, name):
        return not (name in self.name_to_obj)

    @property
    def name_to_obj(self) -> dict[str, Any]:
        return copy(self._name_to_obj)

    @property
    def obj_to_name(self) -> dict[Any, str]:
        return copy(self._obj_to_name)


GNM = GlobalNamesManager()


def default_syntax_checker(value: str) -> Any:
    value_got = value
    found_identifier_candidates = re.findall(r'\w+', value)
    for fic in found_identifier_candidates:
        if fic in GNM.name_to_obj:
            value = value.replace(fic, 'GNM.name_to_obj["{}"]'.format(fic))
    try:
        eval_result = eval(value)
    except NameError:
        raise SyntaxCellError('Syntax error when parsing ' + value_got)
    else:
        return eval_result


def name_syntax_checker(value: str, cls: type) -> str:
    prefix = cls.__name__ + '_'
    if not re.fullmatch(r'\w+', value):
        raise SyntaxCellError('Name have to consists of alphas, nums and _')
    if not value.startswith(prefix):
        raise SyntaxCellError('Name have to begin from ClassName_')
    if value == prefix:
        raise SyntaxCellError('Name cannot be == prefix; add specification to end')
    if not GNM.check_new_name(value):
        raise SyntaxCellError('Name {} already exists'.format(value))
    return value


def default_type_checker(value: Any, req_cls_str: str) -> Any:
    if not type_verification(req_cls_str, value):
        raise TypeCellError('Given value type is not equal to required type')


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
            GNM.remove_obj_name(instance)
        prefix = instance.__class__.__name__ + '_'
        if name_candidate == 'auto_name':
            i = self.start_index
            while True:
                if i < 1:
                    name_candidate = '{}{}'.format(prefix, '0' * (1 - i))
                else:
                    name_candidate = '{}{}'.format(prefix, i)
                if GNM.check_new_name(name_candidate):
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
            assert GNM.check_new_name(name_candidate), 'Name {} already exists'.format(name_candidate)
        instance._name = name_candidate
        GNM.register_obj_name(instance, name_candidate)


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
        if fic in GNM.name_to_obj:
            str_with_replaced_id = str_with_replaced_id.replace(fic, 'GNM.name_to_obj["{}"]'.format(fic))
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


class CellChecker:
    def __init__(self, f_check_syntax=None, f_check_type=None, f_check_semantic=None):
        self.f_check_syntax = f_check_syntax
        self.f_check_type = f_check_type
        self.f_check_semantic = f_check_semantic

    def check_value(self, value: str):
        result = None
        if self.f_check_syntax:
            result = self.f_check_syntax(value)
        if self.f_check_type:
            self.f_check_type(result)
        if self.f_check_semantic:
            self.f_check_semantic(result)
        return result


class NameCellChecker(CellChecker):
    def __init__(self, cls: type):
        super().__init__(partial(name_syntax_checker, cls=cls))


class DefaultCellChecker(CellChecker):
    def __init__(self, req_cls_str: str):
        super().__init__(default_syntax_checker, partial(default_type_checker, req_cls_str=req_cls_str))


def name_auto_setter(cls: Any, start_index: int = 1):
    prefix = cls.__name__ + '_'
    i = start_index
    while True:
        if i < 1:
            auto_name = '{}{}'.format(prefix, '0' * (1 - i))
        else:
            auto_name = '{}{}'.format(prefix, i)
        if GNM.check_new_name(auto_name):
            break
        else:
            i += 1
    return auto_name


class AutoValueSetter:
    def __init__(self, f_set_function=None):
        self.f_set_function = f_set_function

    def get_auto_value(self):  # , *args, **kwargs
        return self.f_set_function()  # *args, **kwargs


class NameAutoSetter(AutoValueSetter):
    def __init__(self, cls: Any, start_index: int = 1):
        super().__init__(partial(name_auto_setter, cls=cls, start_index=start_index))


class Cell:

    @strictly_typed
    def __init__(self, name: str, str_value: str = '',
                 checker: Optional[CellChecker] = None,
                 auto_setter: Optional[AutoValueSetter] = None) -> None:
        self._name = name
        self._str_value = str_value
        self._active = False
        self._is_suggested_value = False

        self._checker = checker
        self._auto_setter = auto_setter

        self._status_check = ''
        self._value = None

    @property
    def name(self):
        return self._name

    @property
    def str_value(self) -> str:
        return self._str_value

    @str_value.setter
    def str_value(self, val: str):
        self._is_suggested_value = False
        self._str_value = val
        if val == '':
            self._status_check = ''

    @property
    def is_suggested_value(self) -> bool:
        return self._is_suggested_value

    @property
    def active(self):
        return self._active

    def activate(self):
        if self.value is None:
            self.auto_set_value()
            self._is_suggested_value = True
        self._active = True

    def deactivate(self):
        self._active = False

    @property
    def checker(self):
        return self._checker

    @property
    def auto_setter(self):
        return self._auto_setter

    @property
    def status_check(self) -> str:
        return self._status_check

    @property
    def value(self):
        return self._value

    def check_value(self):
        if self.checker:
            try:
                result = self.checker.check_value(self.str_value)
            except CellError as ce:
                self._status_check = ce.args[0]
                self._value = None
            else:
                self._status_check = ''
                self._value = result

    def auto_set_value(self):
        if self.auto_setter:
            self.str_value = self.auto_setter.get_auto_value()
            self.check_value()


if __name__ == '__main__':
    class A:
        pass


    a = A()
    # cc_1 = CellChecker(partial(name_syntax_checker, cls=A))
    # cc_2 = CellChecker(default_syntax_checker, partial(default_type_checker, req_cls_str='str'))
    cc_1 = NameCellChecker(A)
    cc_2 = DefaultCellChecker('int')
    print(cc_1.check_value("A_r"))
    print(cc_2.check_value("13"))
    nas = NameAutoSetter(A)
    GNM.register_obj_name('A_1', a)
    print(nas.get_auto_value())

    # tc = TypedCell('tc', 'str', '13')
    # print(tc.__dict__)
