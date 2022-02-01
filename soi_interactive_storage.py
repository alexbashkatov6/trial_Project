from collections import OrderedDict
from typing import Optional, Type
import os
import pandas as pd
from copy import copy

from soi_objects import StationObjectImage, CoordinateSystemSOI

from config_names import GLOBAL_CS_NAME


class DefaultOrderedDict(OrderedDict):
    def __init__(self, default_type: Type):
        super().__init__()
        self.default_type = default_type

    def __getitem__(self, key):
        if key not in self.keys():
            self[key] = self.default_type()
        return super().__getitem__(key)


class SOIInteractiveStorage:
    def __init__(self):
        self.gcs = CoordinateSystemSOI()
        self.gcs._name = GLOBAL_CS_NAME
        self._soi_objects: list[StationObjectImage] = [self.gcs]
        # self._soi_objects: OrderedDict[str, OrderedDict[str, StationObjectImage]] = DefaultOrderedDict(OrderedDict)

    def read_station_config(self, dir_name: str):
        folder = os.path.join(os.getcwd(), dir_name)
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
                    setattr(new_obj, attr_name, attr_val)
                self._soi_objects.append(new_obj)

    @property
    def soi_objects(self) -> list[StationObjectImage]:
        return self._soi_objects

    @property
    def copied_soi_objects(self) -> list[StationObjectImage]:
        return [copy(soi_object) for soi_object in self._soi_objects]


SOI_S = SOIInteractiveStorage()


class SOISelector:
    """ selected object editing """
    def __init__(self):
        self.current_object: Optional[StationObjectImage] = None
        self.is_new_object = True

    def create_empty_object(self, cls_name: str):
        assert cls_name in SOI_S.soi_objects, "Class name not found"
        cls: Type[StationObjectImage] = eval(cls_name)
        self.current_object: StationObjectImage = cls()
        self.is_new_object = True

    def edit_existing_object(self, obj_name: str):
        self.current_object = SOI_S.get_object(obj_name)
        self.is_new_object = False

    def attrib_dict_possible_values(self):
        if not self.current_object:
            return OrderedDict()
        return self.current_object.dict_possible_values

    def attrib_dict_values(self):
        if not self.current_object:
            return OrderedDict()
        return self.current_object.dict_values
