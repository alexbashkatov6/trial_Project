from __future__ import annotations
from typing import Union
from dataclasses import dataclass


@dataclass
class AttribProperties:
    name: str = ""
    suggested_value: str = ""
    last_input_value: str = ""
    last_confirmed_value: str = ""
    check_status: str = ""


# self.possible_values = ["red", "green", "blue"]


class BoundedDescriptor:

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner) -> Union[list[AttribProperties], BoundedDescriptor]:
        if not instance:
            return self
        result = []
        i = 0
        while True:
            attr_candidate_name = "_{}_{}".format(self.name[:-1], i)
            if attr_candidate_name not in instance.__dict__:
                break
            else:
                result.append(instance.__dict__[attr_candidate_name])
                i += 1
        return result


class LightDescriptor:
    def __init__(self):
        self.possible_values = ["red", "green", "blue"]


def get_all_attr_values(instance, attr_name):
    result = []
    i = 0
    while True:
        attr_candidate_name = "_{}_{}".format(attr_name[:-1], i)
        if attr_candidate_name not in instance.__dict__:
            break
        else:
            result.append(instance.__dict__[attr_candidate_name])
            i += 1
    return result


class IndividualDescriptor:
    pass


class BaseClass:
    light = IndividualDescriptor()


class MyClass(BaseClass):

    def bounded_descriptor_list_attribute(self, attr_name: str) -> bool:
        index = attr_name.rfind("_")
        if index == -1:
            return False
        attr_descriptor_name = attr_name[:index] + "_list"
        try:
            descriptor = getattr(self.__class__, attr_descriptor_name)
        except AttributeError:
            print("AttributeError, descriptor not found")
            return False
        else:
            assert isinstance(descriptor, BoundedDescriptor)
            descriptor: BoundedDescriptor
            assert descriptor.is_list
            return True
    #
    # def __setattr__(self, key: str, value):
    #     if self.bounded_descriptor_list_attribute(key):
    #         pass
    #     else:
    #         object.__setattr__(self, key, value)

        # for cls_attr_name in self.__class__.__dict__:
        #     cls_attr_name: str
        #     if cls_attr_name.startswith("__"):
        #         continue
        #     if key.startswith(cls_attr_name[:-1]) and
        #     isinstance(descr := self.__class__.__dict__[cls_attr_name], BoundedDescriptor):
        #         descr.__set__(self, value)
        #     else:
        #         object.__setattr__(self, key, value)

    def __getattr__(self, item: str):
        pass

    def __delattr__(self, item: str):
        pass



mc = MyClass()
mc.light_1 = 45
print(mc.__dict__)
mc.c = 45
print(mc.__dict__)

print("sdsd".rfind("_"))
# del mc.light_1
# print(mc.__dict__)

# mc.d1 = 10
# print(mc.d2)

# "sdsd".removeprefix()
# if a := "lala":
#     print(a)
#     print("success")
#
# from dataclasses import dataclass, field
# from typing import List
#
# @dataclass  # (frozen=True)
# class Book:
#     title: str = "Default"
#     author: str = "Default"
#
# book = Book()
# book.title = "sdasd"
# print(book.title)
#
# @dataclass
# class Bookshelf:
#     books: List[Book] = field(default_factory=list)

# class Descr:
#     def __set_name__(self, owner, name):
#         self.name = name
#
#     def __get__(self, instance, owner):
#         if not instance:
#             return self
#         return 20
#
#     # def __set__(self, instance, value):
#     #     setattr(instance, "_{}".format(self.name), value)
#
#
# class MyClass:
#     d = Descr()
#
#     def __init__(self):
#         pass
#         # self.d = 42
#
# mc = MyClass()

# print(mc.d)

# return self._get_list(instance)

# def __set__(self, instance, value: str):
#     print("set here")

# def _get_list(self, instance) -> list[AttribProperties]:
#     result = []
#     i = 0
#     while True:
#         attr_candidate_name = "_{}_{}".format(self.name[:-1], i)
#         if attr_candidate_name not in instance.__dict__:
#             break
#         else:
#             result.append(instance.__dict__[attr_candidate_name])
#             i += 1
#     return result

# def set_list_index_value(self, instance, index, value: str):
#     attr_prop_list = self._get_list(instance)


# requirements = ["1", "2", "3"]

a = [1 , 2, 3]
a.insert(1, 4)
print(a)
print(float("inf"))
print("-344".isnumeric())
