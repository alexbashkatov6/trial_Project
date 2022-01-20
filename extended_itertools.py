from __future__ import annotations
from collections.abc import Iterable, Callable


class EIError(Exception):
    pass


class EINotFoundError(EIError):
    pass


class EIManyFoundError(EIError):
    pass


def recursive_map(f: Callable, collect: Iterable):
    type_result = type(collect)
    result = []
    for c in collect:
        if (not isinstance(c, Iterable)) or isinstance(c, str):
            result.append(f(c))
        else:
            result.append(recursive_map(f, c))
    return type_result(result)


def recursive_filter(f: Callable, collect: Iterable):
    type_result = type(collect)
    result = []
    for c in collect:
        if (not isinstance(c, Iterable)) or isinstance(c, str):
            if f(c):
                result.append(c)
        else:
            result.append(recursive_filter(f, c))
    return type_result(result)


def flatten(collect):
    for x in collect:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x


def single_element(f: Callable, collect: Iterable):
    result = list(flatten(recursive_filter(f, collect)))
    if len(result) < 1:
        raise EINotFoundError("Element not found")
    if len(result) > 1:
        raise EIManyFoundError("Found more then 1 element")
    return result[0]


if __name__ == "__main__":
    a = [1, 2, [3, [5, 6]], 4]
    b = [9, 1, [3, [5, 8]], 4]

    def fun(x):
        return x+1

    def fun_bool(x):
        return x > 2

    def eq_to_2(x):
        return x == 2

    print(recursive_map(fun, a))
    print(recursive_filter(fun_bool, a))
    print(list(flatten(a)))
    print(single_element(eq_to_2, a))
    # print(single_element(eq_to_2, b))
