from dataclasses import dataclass


@dataclass
class AttributeData:
    cls_name: str
    obj_name: str
    attr_name: str
    index: str = -1
