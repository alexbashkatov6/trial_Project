from __future__ import annotations
from typing import Any, Optional, Union
from functools import wraps
import inspect

__all__ = ['strictly_typed', 'Any', 'Optional', 'Union', 'OneOfString']


class OneOfString:
    def __init__(self, item):
        pass


def arg_verification(string_requirement, value, function):
    def square_brackets_handling(sr):
        if not ('[' in sr):
            return []
        else:
            in_square = sr[sr.find('[')+1:sr.find(']')]
            return [row_str.strip(' \'') for row_str in in_square.split(',')]

    def name_is_known_in_func_module(str_name, func):
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
        if (str_name == 'None') and (val is None):
            return True
        cls = name_is_known_in_func_module(str_name, func)
        assert cls, 'Name {} is unknown'.format(str_name)
        return isinstance(val, cls)

    sq_br_res = square_brackets_handling(string_requirement)
    if not sq_br_res:
        if string_requirement == 'Any':
            return
        assert class_check(string_requirement, value, function), \
            'Class check {} failed for value {}'.format(string_requirement, value)
        return
    else:
        if string_requirement.startswith('Optional'):
            if value is None:
                return
            else:
                assert class_check(sq_br_res[0], value, function), \
                    'Class check {} failed for value {}'.format(string_requirement, value)
                return
        if string_requirement.startswith('Union'):
            if (value is None) and ('None' in sq_br_res):
                return
            class_founded = False
            for varint_cls in sq_br_res:
                class_founded |= class_check(varint_cls, value, function)
            assert class_founded, 'Class check {} failed for value {}'.format(string_requirement, value)
            return
        if string_requirement.startswith('list'):
            assert type(value) == list, 'Should be list: {}'.format(value)
            assert len(sq_br_res) == 1, 'Only single type {} supported for list'.format(value)
            for element in value:
                assert class_check(sq_br_res[0], element, function), \
                    'Class check {} failed for value {} in list'.format(string_requirement, element)
            return
        if string_requirement.startswith('set'):
            assert type(value) == set, 'Should be set: {}'.format(value)
            assert len(sq_br_res) == 1, 'Only single type {} supported for set'.format(value)
            for element in value:
                assert class_check(sq_br_res[0], element, function), \
                    'Class check {} failed for value {} in set'.format(string_requirement, element)
            return
        if string_requirement.startswith('tuple'):
            assert type(value) == tuple, 'Should be tuple: {}'.format(value)
            assert len(value) == len(sq_br_res), \
                'Not equal count of elements in tuple {} and requirements {}'.format(value, sq_br_res)
            for i, element in enumerate(value):
                assert class_check(sq_br_res[i], element, function), \
                    'Class check {}({}) failed for value {} in tuple'.format(string_requirement, sq_br_res[i], element)
            return
        if string_requirement.startswith('dict'):
            assert type(value) == dict, 'Should be dict: {}'.format(value)
            assert len(sq_br_res) == 2, 'Only double type {} supported for dict'.format(value)
            for d_key, d_val in value.items():
                assert class_check(sq_br_res[0], d_key, function), \
                    'Class check {} failed for key {} in dict'.format(string_requirement, d_key)
                assert class_check(sq_br_res[1], d_val, function), \
                    'Class check {} failed for value {} in dict'.format(string_requirement, d_val)
            return
        if string_requirement.startswith('OneOfString'):
            assert value in sq_br_res, 'OneOfString value {} not in {}'.format(value, sq_br_res)
            return


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
            arg_verification(annotats[name], arg_val, function)
        result = function(*args, **kwargs)
        arg_verification(annotats["return"], result, function)
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

    print(my_func(4, {'5': 5, '6': 6}))
