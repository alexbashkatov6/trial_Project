from collections import OrderedDict
import os
import pandas as pd

from soi_objects import StationObjectImage, ComplexAttrError
from default_ordered_dict import DefaultOrderedDict
from form_exception_message import form_message_from_error
from attribute_object_key import AttributeKey


class ReadFileNameError(Exception):
    pass


class RFNoNameError(ReadFileNameError):
    pass


class RFNameRepeatingError(ReadFileNameError):
    pass


class RFGetComplexAttrError(ReadFileNameError):
    pass


class RFNotAllComplexAttrError(ReadFileNameError):
    pass


class RFDublicateComplexAttrError(ReadFileNameError):
    pass


def read_station_config(dir_name: str) -> DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]]:
    result: DefaultOrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)
    folder = os.path.join(os.getcwd(), dir_name)
    for cls in StationObjectImage.__subclasses__():
        cls_name_soi = cls.__name__
        cls_name_del_soi = cls_name_soi.replace("SOI", "")
        file = os.path.join(folder, "{}.xlsx".format(cls_name_del_soi))
        df: pd.DataFrame = pd.read_excel(file, dtype=str, keep_default_na=False)
        obj_dict_list: list[OrderedDict[str, str]] = df.to_dict('records', OrderedDict)
        for obj_dict in obj_dict_list:
            new_obj = cls()
            complex_attr_keys_set = set([cap.name for cap in new_obj.object_prop_struct.attrib_list])
            if "name" not in obj_dict:
                raise RFNoNameError("No column 'name'")
            for attr_name, attr_val in obj_dict.items():
                if "." in attr_name:
                    raise RFDublicateComplexAttrError("Attrib '{}' duplication in file"
                                                      .format(attr_name[:attr_name.index(".")]))
                attr_name = attr_name.strip()
                attr_val = attr_val.strip()
                try:
                    complex_attr_prop = new_obj.get_complex_attr_prop(attr_name)
                except ComplexAttrError as e:
                    raise RFGetComplexAttrError(e.args[0])
                complex_attr_keys_set -= {attr_name}
                complex_attr_prop.temporary_value = attr_val
                if attr_name == "name":
                    if attr_val in result[cls_name_soi]:
                        raise RFNameRepeatingError("Name {} repeats".format(attr_val))
                    result[cls_name_soi][attr_val] = new_obj
            if complex_attr_keys_set:
                raise RFNotAllComplexAttrError("Complex attributes '{}' not found in file".format(", ".join(complex_attr_keys_set)))

    return result


def make_xlsx_templates(dir_name: str):
    # needs to reimplement because of absence of enum values
    folder = os.path.join(os.getcwd(), dir_name)
    for cls in StationObjectImage.__subclasses__():
        name_soi = cls.__name__
        name_del_soi = name_soi.replace("SOI", "")
        file = os.path.join(folder, "{}.xlsx".format(name_del_soi))
        max_possible_values_length = 0
        for val_list in cls.dict_possible_values.values():
            l_ = len(val_list)
            if l_ > max_possible_values_length:
                max_possible_values_length = l_
        od = OrderedDict([("name", [""]*max_possible_values_length)])
        for key, val_list in cls.dict_possible_values.items():
            val_list.extend([""]*(max_possible_values_length-len(val_list)))
            od[key] = val_list
        df = pd.DataFrame(data=od)
        df.to_excel(file, index=False)


if __name__ == "__main__":
    cls_obj_dict = read_station_config("station_in_config")
    # print(cls_obj_dict)
    # print(cls_obj_dict["LineSOI"]["Line_2"].points)
    # print(cls_obj_dict["PointSOI"]["Point_14"].active_attrs)
    # print(cls_obj_dict["PointSOI"]["Point_15"].active_attrs)
    # print(cls_obj_dict["LightSOI"]["M1"].colors)
