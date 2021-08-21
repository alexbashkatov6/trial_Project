from functools import wraps
import inspect

def strictly_typed(function):
    annotations = function.__annotations__
    arg_spec = inspect.getfullargspec(function)
    # print('arg_spec', arg_spec)
    assert "return" in annotations, "missing type for return value"
    for arg in arg_spec.args + arg_spec.kwonlyargs:
        if arg == 'self':
            continue
        assert arg in annotations, ("missing type for parameter '" + arg + "'")
    @wraps(function)
    def wrapper(*args, **kwargs):
        for name, arg in (list(zip(arg_spec.args, args)) + list(kwargs.items())):
            if name == 'self':
                print('here')
                continue
            print('PolarGraph' in globals())
            print('name,arg = ', name, arg, annotations[name])
            print('name,arg = ', type(name), type(arg), type(annotations[name])) # , type(eval(annotations[name]))
            assert isinstance(arg, annotations[name]), ("expected argument '{0}' of {1} got {2}"
                                                        .format(name, annotations[name], type(arg)))
        result = function(*args, **kwargs)
        assert isinstance(result, annotations["return"]), ("expected return of {0} got {1}"
                                                           .format(annotations["return"], type(result)))
        return result
    return wrapper