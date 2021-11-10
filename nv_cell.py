from __future__ import annotations
import re
from copy import copy
from functools import partial

from nv_errors import CellError, TypeCellError, SyntaxCellError
from nv_bounded_string_set_class import bounded_string_set
from nv_typing import *

BSSCellType = bounded_string_set('BSSCellType', [['default'],
                                                 ['name'],
                                                 ['common_splitter'],
                                                 ['bool_splitter']])


# def default_syntax_checker(value: str) -> Any:
#     value_got = value
#     found_identifier_candidates = re.findall(r'\w+', value)
#     for fic in found_identifier_candidates:
#         if fic in GNM.name_to_obj:
#             value = value.replace(fic, 'GNM.name_to_obj["{}"]'.format(fic))
#     try:
#         eval_result = eval(value)
#     except SyntaxError:
#         raise SyntaxCellError('Syntax error when parsing ' + value_got)
#     except NameError:
#         raise SyntaxCellError('Name error when parsing ' + value_got)
#     else:
#         return eval_result
#
#
# def splitter_syntax_checker(value: str, cls: type):
#     if value not in cls.possible_strings:
#         raise SyntaxCellError('Value of splitter not in possible values{}'.format(cls.possible_strings))
#     return value
#
#
# def bool_syntax_checker(value: str, cls: type):
#     if value not in cls.possible_strings:
#         raise SyntaxCellError('Value of splitter not in possible values {}'.format(cls.possible_strings))
#     return eval(value)
#
#
# def name_syntax_checker(value: str, obj: Any) -> str:
#     cls = obj.__class__
#     if (obj in GNM.obj_to_name) and (value == GNM.obj_to_name[obj]):
#         return value
#     prefix = cls.__name__ + '_'
#     if not re.fullmatch(r'\w+', value):
#         raise SyntaxCellError('Name have to consists of alphas, nums and _')
#     if not value.startswith(prefix):
#         raise SyntaxCellError('Name have to begin from ClassName_')
#     if value == prefix:
#         raise SyntaxCellError('Name cannot be == prefix; add specification to end')
#     if not GNM.check_new_name(value):
#         raise SyntaxCellError('Name {} already exists'.format(value))
#     return value
#
#
# def default_type_checker(value: Any, req_cls_str: str) -> None:
#     if not type_verification(req_cls_str, value):
#         raise TypeCellError('Given str_value type is not equal to required type')


# class CellChecker:
#     def __init__(self, f_check_syntax=None, f_check_type=None, f_check_semantic_list: list = None):
#         self.f_check_syntax = f_check_syntax
#         self.f_check_type = f_check_type
#         if f_check_semantic_list is None:
#             self.f_check_semantic_list = []
#         else:
#             self.f_check_semantic_list = f_check_semantic_list
#         self._req_class_str = None
#
#     def add_semantic_checker(self, f_check_semantic: Callable):
#         self.f_check_semantic_list.append(f_check_semantic)
#
#     def check_value(self, str_value: str):
#         result = None
#         if self.f_check_syntax:
#             result = self.f_check_syntax(str_value)
#         if self.f_check_type:
#             self.f_check_type(result)
#         for f_check_semantic in self.f_check_semantic_list:
#             f_check_semantic(str_value, result)
#         return result
#
#     @property
#     def req_class_str(self):
#         return self._req_class_str
#
#
# class NameCellChecker(CellChecker):
#     def __init__(self, obj: Any):
#         super().__init__(partial(name_syntax_checker, obj=obj))
#         self._req_class_str = 'str'  # .format(cls.__name__)
#
#
# class SplitterCellChecker(CellChecker):
#     def __init__(self, cls: type):
#         super().__init__(partial(splitter_syntax_checker, cls=cls))
#         self._req_class_str = cls.__name__
#
#
# class BoolCellChecker(CellChecker):
#     def __init__(self, cls: type):
#         super().__init__(partial(bool_syntax_checker, cls=cls))
#         self._req_class_str = cls.__name__
#
#
# class DefaultCellChecker(CellChecker):
#     def __init__(self, req_cls_str: str):
#         super().__init__(default_syntax_checker, partial(default_type_checker, req_cls_str=req_cls_str))
#         self._req_class_str = req_cls_str
#
#
# def name_auto_setter(cls: Any, start_index: int = 1):
#     prefix = cls.__name__ + '_'
#     i = start_index
#     while True:
#         if i < 1:
#             auto_name = '{}{}'.format(prefix, '0' * (1 - i))
#         else:
#             auto_name = '{}{}'.format(prefix, i)
#         if GNM.check_new_name(auto_name):
#             break
#         else:
#             i += 1
#     # print('In auto_name', auto_name)
#     return auto_name
#
#
# class AutoValueSetter:
#     def __init__(self, f_set_function=None):
#         self.f_set_function = f_set_function
#
#     def get_auto_value(self):  # , *args, **kwargs
#         return self.f_set_function()  # *args, **kwargs
#
#
# class NameAutoSetter(AutoValueSetter):
#     def __init__(self, cls: Any, start_index: int = 1):
#         super().__init__(partial(name_auto_setter, cls=cls, start_index=start_index))


class Cell:

    @strictly_typed
    def __init__(self, name: str, str_req: str = '', str_value: str = '',
                 cell_type: BSSCellType = BSSCellType('default')) -> None:
        self._name = name
        self._str_req = str_req
        self._str_value = str_value
        self._cell_type = cell_type

        self._active = False
        self._is_suggested_value = False
        self._status_check = ''
        self._eval_buffer = None
        self._value = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val: str):
        self._name = val

    @property
    def cell_type(self):
        return self._cell_type

    @cell_type.setter
    def cell_type(self, val: str):
        self._cell_type = val

    @property
    def str_value(self) -> str:
        return self._str_value

    @str_value.setter
    def str_value(self, val: str):
        self._str_value = val
        # self._is_suggested_value = False
        # self._str_value = val
        # if val == '':
        #     self._status_check = 'empty'

    @property
    def str_req(self) -> str:
        return self._str_req

    @str_req.setter
    def str_req(self, val: str):
        self._str_req = val

    @property
    def is_suggested_value(self) -> bool:
        return self._is_suggested_value

    @is_suggested_value.setter
    def is_suggested_value(self, val: bool):
        self._is_suggested_value = val

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val: bool):
        self._active = val

    # def activate(self):
    #     if self.str_value == '':
    #         self.auto_set_value()
    #     self._active = True
    #
    # def deactivate(self):
    #     self._active = False

    # @property
    # def checker(self):
    #     return self._checker
    #
    # @property
    # def auto_setter(self):
    #     return self._auto_setter

    @property
    def status_check(self) -> str:
        return self._status_check

    @status_check.setter
    def status_check(self, val: str):
        self._status_check = val

    @property
    def eval_buffer(self) -> Any:
        return self._eval_buffer

    @eval_buffer.setter
    def eval_buffer(self, val: Any):
        self._eval_buffer = val

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, val: Any):
        self._value = val

    # def check_value(self):
    #     if self.str_value == '':
    #         self._status_check = 'empty'
    #         self._value = None
    #         return
    #     if self.checker:
    #         try:
    #             result = self.checker.check_value(self.str_value)
    #         except CellError as ce:
    #             self._status_check = ce.args[0]
    #             self._value = None
    #         else:
    #             self._status_check = ''
    #             self._value = result
    #     else:
    #         self._status_check = ''
    #         self._value = self.str_value
    #
    # def auto_set_value(self):
    #     if self.auto_setter:
    #         self.str_value = self.auto_setter.get_auto_value()
    #         self.check_value()
    #         self._is_suggested_value = True

    # @property
    # def req_class_str(self):
    #     if self.checker:
    #         return self.checker.req_class_str


if __name__ == '__main__':
    class A:
        pass


    a = A()
    # cc_1 = CellChecker(partial(name_syntax_checker, cls=A))
    # cc_2 = CellChecker(default_syntax_checker, partial(default_type_checker, req_cls_str='str'))
    # cc_1 = NameCellChecker(A)
    # cc_2 = DefaultCellChecker('int')
    # print(cc_1.check_value("A_r"))
    # print(cc_2.check_value("13"))
    # nas = NameAutoSetter(A)
    # GNM.register_obj_name('A_1', a)
    # print(nas.get_auto_value())

    # tc = TypedCell('tc', 'str', '13')
    # print(tc.__dict__)
