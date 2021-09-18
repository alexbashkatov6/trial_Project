from __future__ import annotations
from typing import Any, Optional, Union
from collections.abc import Iterable
from functools import wraps
import inspect

__all__ = ['strictly_typed', 'Any', 'Optional', 'Union', 'OneOfString']


class OneOfString:
    def __init__(self, item):
        pass
# class OneOfStringClass:
#     def __getitem__(self, item):
#         pass
# OneOfString = OneOfStringClass()


def arg_verification(string_requirement, value, function, first_enter=False):
    def out_bracket_split(string):
        result_of_split = []
        depth_of_bracket = 0
        current_str = ''
        for symbol in string:
            if symbol == ',':
                if not depth_of_bracket:
                    result_of_split.append(current_str.strip(' \''))
                    current_str = ''
                    continue
            if symbol == '[':
                depth_of_bracket += 1
            if symbol == ']':
                depth_of_bracket -= 1
            current_str += symbol
        result_of_split.append(current_str.strip(' \''))
        return result_of_split

    def square_brackets_handling(sr):
        if not ('[' in sr):
            return False
        else:
            in_square = sr[sr.find('[')+1:sr.rfind(']')]
            return out_bracket_split(in_square)

    def get_class(str_name, func):
        try:
            cls = eval(str_name)
        except NameError:
            pass
        else:
            return cls
        try:
            cls = getattr(inspect.getmodule(func), str_name)
        except AttributeError:
            return False
        return cls

    def class_check(str_name, val, func):
        # print('in class check, get str: ', str_name, ', get val: ', val)
        if (str_name == 'None') and (val is None):
            return True
        cls = get_class(str_name, func)
        assert cls, 'Name {} is unknown'.format(str_name)
        return isinstance(val, cls)

    try:
        sq_br_res = square_brackets_handling(string_requirement)  # operat_cls,
        if not sq_br_res:
            if string_requirement == 'Any':
                return True
            assert class_check(string_requirement, value, function), \
                'Cls check failed for req_cls={}, val={}'.format(string_requirement, value)
            return True
        else:
            if string_requirement.startswith('Optional'):
                if value is None:
                    return True
                else:
                    assert arg_verification(sq_br_res[0], value, function), \
                        'Class check {} failed for value {}'.format(string_requirement, value)
                    return True
            if string_requirement.startswith('Union'):
                if (value is None) and ('None' in sq_br_res):
                    return True
                class_founded = False
                for varint_cls in sq_br_res:
                    # print('variants get: ', varint_cls)
                    class_founded |= arg_verification(varint_cls, value, function)
                assert class_founded, 'Class check {} failed for value {}'.format(string_requirement, value)
                return True
            if string_requirement.startswith('list'):
                assert type(value) == list, 'Should be list: {}'.format(value)
                assert len(sq_br_res) == 1, 'Only single type {} supported for list'.format(value)
                for element in value:
                    assert arg_verification(sq_br_res[0], element, function), \
                        'Class check {} failed for value {} in list'.format(string_requirement, element)
                return True
            if string_requirement.startswith('set'):
                assert type(value) == set, 'Should be set: {}'.format(value)
                assert len(sq_br_res) == 1, 'Only single type {} supported for set'.format(value)
                for element in value:
                    assert arg_verification(sq_br_res[0], element, function), \
                        'Class check {} failed for value {} in set'.format(string_requirement, element)
                return True
            if string_requirement.startswith('Iterable'):
                assert issubclass(type(value), Iterable), 'Should be Iterable: {}'.format(value)
                assert len(sq_br_res) == 1, 'Only single type {} supported for Iterable'.format(value)
                for element in value:
                    assert arg_verification(sq_br_res[0], element, function), \
                        'Class check {} failed for value {} in Iterable'.format(string_requirement, element)
                return True
            if string_requirement.startswith('tuple'):
                assert type(value) == tuple, 'Should be tuple: {}'.format(value)
                assert len(value) == len(sq_br_res), \
                    'Not equal count of elements in tuple {} and requirements {}'.format(value, sq_br_res)
                for i, element in enumerate(value):
                    assert arg_verification(sq_br_res[i], element, function), \
                        'Class check {}({}) failed for value {} in tuple'.format(string_requirement, sq_br_res[i], element)
                return True
            if string_requirement.startswith('dict'):
                assert type(value) == dict, 'Should be dict: {}'.format(value)
                assert len(sq_br_res) == 2, 'Only double type {} supported for dict'.format(value)
                for d_key, d_val in value.items():
                    assert arg_verification(sq_br_res[0], d_key, function), \
                        'Class check {} failed for key {} in dict'.format(string_requirement, d_key)
                    assert arg_verification(sq_br_res[1], d_val, function), \
                        'Class check {} failed for value {} in dict'.format(string_requirement, d_val)
                return True
            if string_requirement.startswith('OneOfString'):
                assert value in sq_br_res, 'OneOfString value {} not in {}'.format(value, sq_br_res)
                return True
    except AssertionError as ae:
        if first_enter:
            raise ae
        else:
            return False


def strictly_typed(function):
    annotats = function.__annotations__
    arg_spec = inspect.getfullargspec(function)
    assert "return" in annotats, "missing type for return value"
    for arg in arg_spec.args + arg_spec.kwonlyargs:
        if arg == 'self':
            continue
        assert arg in annotats, ("missing type for parameter '" + arg + "'")

    @wraps(function)
    def wrapper(*args, **kwargs):
        for name, arg_val in (list(zip(arg_spec.args, args)) + list(kwargs.items())):
            if name == 'self':
                continue
            if name == 'name':
                continue
            arg_verification(annotats[name], arg_val, function, True)
        result = function(*args, **kwargs)
        arg_verification(annotats["return"], result, function, True)
        return result
    return wrapper


if __name__ == '__main__':

    @strictly_typed
    def my_func(a: int, b: dict[str, int]) -> str:  # Union[str, int]
        # if b is None:
        #     return str(a)
        # if type(b) == int:
        #     return str(a) + str(b)
        # return str(a) + b.val
        return str(a) + list(b.keys())[0]


    class CoordSyst:
        def __init__(self):
            self.val = '9'


    cs = CoordSyst()

    # print(my_func(4, {'5': 5, '6': 6}))

    @strictly_typed
    def my_func2(a: bool) -> Union[list[str], str]:
        if a:
            return 'lala'
        else:
            return ['la', 'la']

    print('mf2 result = ', my_func2(True), my_func2(False))

    @strictly_typed
    def my_func3(a: bool) -> Optional[set[str]]:
        if a:
            return {'la', 'la'}
        else:
            return None

    print('mf3 result = ', my_func3(True))

    @strictly_typed
    def my_func4(a: bool) -> Optional[dict[tuple[str, str], int]]:
        if a:
            return {('str_1', 'str_1'): 345}
        else:
            return None

    print('mf4 result = ', my_func4(True))

    @strictly_typed
    def my_func5(a: bool) -> Optional[Iterable[int]]:
        if a:
            return [1]
        else:
            return None

    print('mf5 result = ', my_func5(True))

    # def intell_split(string):
    #     result_of_split = []
    #     depth_of_bracket = 0
    #     current_str = ''
    #     for symbol in string:
    #         if symbol == ',':
    #             if not depth_of_bracket:
    #                 result_of_split.append(current_str.strip(' \''))
    #                 current_str = ''
    #                 continue
    #         if symbol == '[':
    #             depth_of_bracket += 1
    #         if symbol == ']':
    #             depth_of_bracket -= 1
    #         current_str += symbol
    #     result_of_split.append(current_str.strip(' \''))
    #     return result_of_split
    #
    # print('intell_split result = ', intell_split('asdsd[kjk, dsdsd sd], dfdsf'))

