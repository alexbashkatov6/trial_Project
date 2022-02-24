from dataclasses import dataclass


@dataclass
class AttributeErrorData:
    cls_name: str
    obj_name: str
    attr_name: str
    index: str = -1
