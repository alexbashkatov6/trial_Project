from dataclasses import dataclass, field


@dataclass
class InterfaceExchange:
    def to_dict(self):
        result = {}
        for key, val in self.__dict__.items():
            if isinstance(val, list):
                result[key] = []
                for item in val:
                    print("item", item)
                    result[key].append(item.to_dict())
            else:
                result[key] = val
        return result


@dataclass
class ObjectProperties(InterfaceExchange):
    name: str = ""
    error_message: str = ""
    attrib_list: list = field(default_factory=list)


@dataclass
class ComplexAttribProperties(InterfaceExchange):
    name: str = ""
    is_list: bool = False
    is_mutable: bool = False
    single_attr_list: list = field(default_factory=list)


@dataclass
class SingleAttribProperties(InterfaceExchange):
    index: int = -1
    str_value: str = ""
    is_suggested: bool = False
    error_message: str = ""


if __name__ == "__main__":
    op = ObjectProperties()
    cap = ComplexAttribProperties()
    sap = SingleAttribProperties()
    op.attrib_list.append(cap)
    cap.single_attr_list.append(sap)
    print(op.to_dict())
