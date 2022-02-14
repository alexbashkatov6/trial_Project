from collections import OrderedDict
import os
import pandas as pd

from new_soi_objects import StationObjectImage
from default_ordered_dict import DefaultOrderedDict


class ReadFileNameError(Exception):
    pass


class RFNoNameError(ReadFileNameError):
    pass


class RFExistingNameError(ReadFileNameError):
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
            assert "name" in obj_dict, "No column 'name'"
            for attr_name, attr_val in obj_dict.items():
                attr_name = attr_name.strip()
                attr_val = attr_val.strip()
                if " " in attr_val:
                    attr_val = attr_val.split(" ")
                if attr_name == "name":
                    if not attr_val:
                        raise RFNoNameError(cls_name_del_soi, "", "name", "No-name-object in class")
                    if attr_val in result[cls_name_soi]:
                        raise RFExistingNameError(cls_name_del_soi, attr_val, "name", "Name already exists")
                    result[cls_name_soi][attr_val] = new_obj
                setattr(new_obj, attr_name, attr_val)
                new_obj.changed_attrib_value(attr_name, attr_val)
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
    print(read_station_config("station_in_config"))
