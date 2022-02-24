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
    objects_list: list = field(default_factory=list)


@dataclass
class ObjectProperties(InterfaceExchange):
    name: str = ""
    error_message: str = ""
    attrib_list: list = field(default_factory=list)


@dataclass
class ComplexAttribProperties(InterfaceExchange):
    name: str = ""
    req_count: int = -1
    is_list: bool = False
    is_mutable: bool = False
    single_attr_list: list = field(default_factory=list)


@dataclass
class SingleAttribProperties(InterfaceExchange):
    index: int = -1
    str_value: str = ""
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
