from dataclasses import dataclass


@dataclass
class ObjectKey:
    cls_name: str
    obj_name: str

    def __hash__(self):
        return hash((self.cls_name, self.obj_name))


@dataclass
class AttributeKey:
    cls_name: str
    obj_name: str
    attr_name: str
    index: str = -1

    def __hash__(self):
        return hash((self.cls_name, self.obj_name, self.attr_name, self.index))


if __name__ == "__main__":
    d = {}
    aad = AttributeKey("1", "1", "1")
    aad_1 = AttributeKey("1", "1", "1")
    d[aad] = 1
    d[aad_1] = 2
    print(d)
    print(aad_1 in [aad])
    # d[aad] = 12
    # print(("1", "2", "3", 45) is ("1", "2", "3", 45))
    # aad_2 = AttributeAccessDict("1", "1", "1")
    # print(aad == aad_2)
