from functools import wraps
import inspect


def get_class(str_value, function=None):
    if str_value == 'Any':
        return
    try:
        req_class = eval(str_value)
    except NameError:
        req_class = getattr(inspect.getmodule(function), str_value)
    return req_class


def strictly_typed(function):
    annotations = function.__annotations__
    arg_spec = inspect.getfullargspec(function)
    assert "return" in annotations, "missing type for return value"
    for arg in arg_spec.args + arg_spec.kwonlyargs:
        if arg == 'self':
            continue
        assert arg in annotations, ("missing type for parameter '" + arg + "'")
    @wraps(function)
    def wrapper(*args, **kwargs):
        for name, arg in (list(zip(arg_spec.args, args)) + list(kwargs.items())):
            if name == 'self':
                continue
            req_arg_class = get_class(annotations[name], function)
            if req_arg_class:
                assert isinstance(arg, req_arg_class), ("expected argument '{0}' of {1} got {2}"
                                                        .format(name, req_arg_class, type(arg)))
        result = function(*args, **kwargs)
        req_resul_class = get_class(annotations["return"], function)
        if req_resul_class:
            assert isinstance(result, req_resul_class), ("expected return of {0} got {1}"
                                                           .format(req_resul_class, type(result)))
        return result
    return wrapper