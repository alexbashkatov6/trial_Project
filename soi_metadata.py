from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InterfaceExchange:
    def to_dict(self):
        result = {}
        for key, val in self.__dict__.items():
            if isinstance(val, list):
                result[key] = []
                for item in val:
                    result[key].append(item.to_dict())
            else:
                result[key] = val
        return result


@dataclass
class ClassProperties(InterfaceExchange):
    name: str = ""
    objects_list: list[ObjectProperties] = field(default_factory=list)


@dataclass
class ObjectProperties(InterfaceExchange):
    name: str = ""  # which is title
    error_message: str = ""
    # creation_readiness: bool = False
    attrib_list: list[ComplexAttribProperties] = field(default_factory=list)


@dataclass
class ComplexAttribProperties(InterfaceExchange):
    name: str = ""  # which is attribute
    active: bool = True
    temporary_value: str = ""
    is_list: bool = False
    is_object: bool = False
    exact_count: int = -1
    min_count: int = -1
    immutable: bool = False
    single_attr_list: list[SingleAttribProperties] = field(default_factory=list)


@dataclass
class SingleAttribProperties(InterfaceExchange):
    index: int = -1

    last_input_str_value: str = ""
    last_confirmed_str_value: str = ""
    suggested_str_value: str = ""
    interface_str_value: str = ""

    is_suggested: bool = False
    is_required: bool = False
    error_message: str = ""


if __name__ == "__main__":
    cp = ClassProperties()
    op = ObjectProperties()
    cap = ComplexAttribProperties()
    sap = SingleAttribProperties()
    cp.objects_list.append(op)
    op.attrib_list.append(cap)
    cap.single_attr_list.append(sap)
    print(cp.to_dict())
