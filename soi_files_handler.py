from collections import OrderedDict
import os
import pandas as pd

from soi_objects import StationObjectImage


def make_xlsx_templates(dir_name: str):
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


def read_station_config(dir_name: str) -> list[StationObjectImage]:
    folder = os.path.join(os.getcwd(), dir_name)
    objs_ = []
    for cls in StationObjectImage.__subclasses__():
        name_soi = cls.__name__
        name_del_soi = name_soi.replace("SOI", "")
        file = os.path.join(folder, "{}.xlsx".format(name_del_soi))
        df: pd.DataFrame = pd.read_excel(file, dtype=str, keep_default_na=False)
        obj_dict_list: list[OrderedDict] = df.to_dict('records', OrderedDict)
        for obj_dict in obj_dict_list:
            new_obj = cls()
            for attr_name, attr_val in obj_dict.items():
                attr_name: str
                attr_val: str
                attr_name = attr_name.strip()
                attr_val = attr_val.strip()
                setattr(new_obj, attr_name, attr_val)  # can be raised custom enum exceptions
            objs_.append(new_obj)
    return objs_


class SOIFilesHandler:
    pass
