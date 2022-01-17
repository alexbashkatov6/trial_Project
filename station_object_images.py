from __future__ import annotations
from typing import Type, Optional, Union
from collections import OrderedDict
from copy import copy
import pandas as pd
import os

from custom_enum import CustomEnum
from two_sided_graph import OneComponentTwoSidedPG, PolarNode
from cell_object import CellObject
from extended_itertools import single_element, recursive_map, flatten

GLOBAL_CS_NAME = "GlobalCS"
STATION_OUT_CONFIG_FOLDER = "station_out_config"
STATION_IN_CONFIG_FOLDER = "station_in_config"

# -------------------------        OBJECT IMAGES CLASSES        ------------------------- #


# ------------        EXCEPTIONS        ------------ #

class NotImplementedCoError(Exception):
    pass


class NoNameCoError(Exception):
    pass


class ExistingNameCoError(Exception):
    pass


class TypeCoError(Exception):
    pass


class SyntaxCoError(Exception):
    pass


class SemanticCoError(Exception):
    pass


class CycleError(Exception):
    pass


# ------------        ENUMS        ------------ #


class CEDependence(CustomEnum):
    dependent = 0
    independent = 1


class CEBool(CustomEnum):
    false = 0
    true = 1


class CEAxisCreationMethod(CustomEnum):
    translational = 0
    rotational = 1


class CEAxisOrLine(CustomEnum):
    axis = 0
    line = 1


class CELightRouteType(CustomEnum):
    train = 0
    shunt = 1


class CELightStickType(CustomEnum):
    mast = 0
    dwarf = 1


class CELightColor(CustomEnum):
    dark = 0
    red = 1
    blue = 2
    white = 3
    yellow = 4
    green = 5


class CEBorderType(CustomEnum):
    standoff = 0
    ab = 1
    pab = 2


# ------------        IMAGES COMMON AGGREGATE ATTRS        ------------ #


class SOIAttrSeqTemplate:
    def __get__(self, instance, owner) -> list[str]:

        if owner == CoordinateSystemSOI:
            return [x.name for x in
                    [CoordinateSystemSOI.cs_relative_to,
                     CoordinateSystemSOI.dependence,
                     CoordinateSystemSOI.x,
                     CoordinateSystemSOI.y,
                     CoordinateSystemSOI.alpha,
                     CoordinateSystemSOI.co_x,
                     CoordinateSystemSOI.co_y]]

        if owner == AxisSOI:
            return [x.name for x in
                    [AxisSOI.cs_relative_to,
                     AxisSOI.creation_method,
                     AxisSOI.y,
                     AxisSOI.center_point,
                     AxisSOI.alpha]]

        if owner == PointSOI:
            return [x.name for x in
                    [PointSOI.on,
                     PointSOI.axis,
                     PointSOI.line,
                     PointSOI.x]]

        if owner == LineSOI:
            return [x.name for x in
                    [LineSOI.points]]

        if owner == LightSOI:
            return [x.name for x in
                    [LightSOI.light_route_type,
                     LightSOI.center_point,
                     LightSOI.direct_point,
                     LightSOI.colors,
                     LightSOI.light_stick_type]]

        if owner == RailPointSOI:
            return [x.name for x in
                    [RailPointSOI.center_point,
                     RailPointSOI.dir_plus_point,
                     RailPointSOI.dir_minus_point]]

        if owner == BorderSOI:
            return [x.name for x in
                    [BorderSOI.point,
                     BorderSOI.border_type]]

        if owner == SectionSOI:
            return [x.name for x in
                    [SectionSOI.border_points]]

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class SOIActiveAttrs:
    def __get__(self, instance, owner):
        assert instance, "Only for instance"
        instance: StationObjectImage
        instance._active_attrs = instance.attr_sequence_template

        if owner == CoordinateSystemSOI:
            instance: CoordinateSystemSOI
            if instance.dependence == CEDependence.dependent:
                instance._active_attrs.remove(CoordinateSystemSOI.alpha.name)
            else:
                instance._active_attrs.remove(CoordinateSystemSOI.x.name)
                instance._active_attrs.remove(CoordinateSystemSOI.y.name)

        if owner == AxisSOI:
            instance: AxisSOI
            if instance.creation_method == CEAxisCreationMethod.rotational:
                instance._active_attrs.remove(AxisSOI.y.name)
            else:
                instance._active_attrs.remove(AxisSOI.alpha.name)
                instance._active_attrs.remove(AxisSOI.center_point.name)

        if owner == PointSOI:
            instance: PointSOI
            if instance.on == CEAxisOrLine.axis:
                instance._active_attrs.remove(PointSOI.line.name)
            else:
                instance._active_attrs.remove(PointSOI.axis.name)

        return instance._active_attrs

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class SOIListPossibleValues:
    def __get__(self, instance, owner):
        if instance is None:
            result = OrderedDict()
            for attr_ in owner.attr_sequence_template:
                attrib = getattr(owner, attr_)
                if attrib.enum:
                    result[attr_] = attrib.enum.possible_values
                else:
                    result[attr_] = []
        else:
            instance: StationObjectImage
            result = OrderedDict()
            for active_attr in instance.active_attrs:
                attrib = getattr(instance, active_attr)
                if isinstance(attrib, CustomEnum):
                    result[active_attr] = attrib.possible_values
                else:
                    result[active_attr] = []
        return result

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class SOIListValues:
    def __get__(self, instance, owner):
        assert instance, "Only for instance"
        instance: StationObjectImage
        result = OrderedDict()
        for active_attr in instance.active_attrs:
            result[active_attr] = getattr(instance, active_attr)
        return result

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


def predict_name(instance: StationObjectImage) -> str:
    i = 0
    cls_name = instance.__class__.__name__
    while True:
        i += 1
        predicted_name = "{}_{}".format(cls_name, i)
        if predicted_name not in SOIS.names_list:
            return predicted_name


class SOIName:
    def __get__(self, instance, owner):
        assert instance, "Only for instance"
        return getattr(instance, "_name")

    def __set__(self, instance, value: str):
        if value in SOIS.names_list:
            raise ExistingNameCoError("Name {} already exists".format(value))
        instance._name = value


# ------------        BASE ATTRIBUTE DESCRIPTOR        ------------ #


class BaseAttrDescriptor:

    def __init__(self, expected_type_or_enum: Union[str, CustomEnum, tuple[str, str]] = None):
        self.enum = None
        self.expected_type = None
        self.default_value = None
        if expected_type_or_enum:
            if isinstance(expected_type_or_enum, CustomEnum):
                self.enum = expected_type_or_enum
            elif isinstance(expected_type_or_enum, tuple):
                self.expected_type: str = expected_type_or_enum[0]
                self.default_value: str = expected_type_or_enum[1]
            else:
                self.expected_type: str = expected_type_or_enum

    def __get__(self, instance, owner):
        if not instance:
            return self
        elif hasattr(instance, "_no_eval_mode_"+self.name):  # str-value
            return getattr(instance, "_str_"+self.name)
        elif hasattr(instance, "_"+self.name):
            return getattr(instance, "_"+self.name)
        elif self.enum:
            setattr(instance, "_"+self.name, self.enum)
            return getattr(instance, "_"+self.name)
        elif hasattr(instance, "predicted_"+self.name):  # predicted
            return getattr(instance, "_predicted_"+self.name)
        # elif self.default_value:  # default
        #     return self.default_value
        else:
            return None

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance: StationObjectImage, value: str):
        value = value.strip()
        setattr(instance, "_str_"+self.name, value.replace("_str_", ""))

        """ for stage building DG - no evaluations """
        if value.startswith("_str_") and value.endswith("_str_"):
            setattr(instance, "_no_eval_mode_" + self.name, True)
            setattr(instance, "_" + self.name, value.replace("_str_", ""))
            return
        if hasattr(instance, "_no_eval_mode_" + self.name):
            delattr(instance, "_no_eval_mode_" + self.name)

        assert self.name in instance.active_attrs, "Attribute for set should be active"

        """ for enum values """
        if self.enum:
            inst_enum: CustomEnum = getattr(instance, self.name)
            setattr(instance, "_" + self.name, type(inst_enum)(value))
        elif self.expected_type:
            if self.expected_type == "complex_type":
                return
            else:
                expected_type = eval(self.expected_type)  # eval because Py-class cannot directly contain its name

            if issubclass(expected_type, StationObjectImage):
                if value in SOIS.names_list:
                    obj = SOIS.get_object(value)
                    if isinstance(obj, expected_type):
                        setattr(instance, "_eval_" + self.name, obj)
                    else:
                        raise TypeCoError("Type of given object {} not satisfy type requirement {}"
                                          .format(value, expected_type))
                else:
                    raise TypeCoError("Type of given object {} not satisfy type requirement {}"
                                      .format(value, expected_type))
            elif expected_type in [str, int, float]:
                try:
                    val = expected_type(value)
                except ValueError:
                    raise TypeCoError("Type of given object {} not satisfy type requirement {}"
                                      .format(value, expected_type))
                setattr(instance, "_eval_" + self.name, val)
            else:
                assert False, "StationObject type or str, int, float expected"

            if self.__class__.__set__ is BaseAttrDescriptor.__set__:
                self.push_eval_to_value(instance)
        else:
            assert False, "No requirements found"

    def get_str_value(self, instance: StationObjectImage):
        return getattr(instance, "_str_" + self.name)

    def get_eval_value(self, instance: StationObjectImage):
        return getattr(instance, "_eval_" + self.name)

    def push_eval_to_value(self, instance: StationObjectImage):
        setattr(instance, "_" + self.name, getattr(instance, "_eval_" + self.name))


# ------------        PARTIAL ATTRIBUTE DESCRIPTORS        ------------ #


class CsCsRelTo(BaseAttrDescriptor):
    pass


class CsDepend(BaseAttrDescriptor):
    pass


class CsX(BaseAttrDescriptor):
    pass


class CsY(BaseAttrDescriptor):
    pass


class CsAlpha(BaseAttrDescriptor):
    def __set__(self, instance, value):
        raise NotImplementedCoError


class CsCoX(BaseAttrDescriptor):
    pass


class CsCoY(BaseAttrDescriptor):
    pass


class AxCsRelTo(BaseAttrDescriptor):
    pass


class AxCrtMethod(BaseAttrDescriptor):
    pass


class AxY(BaseAttrDescriptor):
    pass


class AxCenterPoint(BaseAttrDescriptor):

    def __set__(self, instance, value):
        super().__set__(instance, value)
        if hasattr(instance, "_no_eval_mode_" + self.name):
            return
        point: PointSOI = self.get_eval_value(instance)
        if point.on != "axis":
            raise SemanticCoError("Center point should be on Axis")
        else:
            self.push_eval_to_value(instance)


class AxAlpha(BaseAttrDescriptor):
    pass


class PntOn(BaseAttrDescriptor):
    pass


class PntAxis(BaseAttrDescriptor):
    pass


class PntLine(BaseAttrDescriptor):
    pass


class PntX(BaseAttrDescriptor):

    def __set__(self, instance, value):
        super().__set__(instance, value)
        if hasattr(instance, "_no_eval_mode_" + self.name):
            return
        x: str = self.get_str_value(instance)
        if x.startswith("PK"):
            try:
                hund_meters = x[x.index("_")+1:x.index("+")]
                meters = x[x.index("+"):]
                hund_meters = int(hund_meters)
                meters = int(meters)
            except ValueError:
                raise TypeCoError("Expected int value or picket 'PK_xx+xx'")
            setattr(instance, "_"+self.name, hund_meters*100 + meters)
        else:
            try:
                meters = int(x)
            except ValueError:
                raise TypeCoError("Expected int value or picket 'PK_xx+xx'")
            setattr(instance, "_"+self.name, meters)


class LinePoints(BaseAttrDescriptor):
    pass


class LightRouteType(BaseAttrDescriptor):
    pass


class LightStickType(BaseAttrDescriptor):
    pass


class LightCenterPoint(BaseAttrDescriptor):
    pass


class LightDirectionPoint(BaseAttrDescriptor):
    pass


class LightColors(BaseAttrDescriptor):
    pass


class RailPCenterPoint(BaseAttrDescriptor):
    pass


class RailPDirPlusPoint(BaseAttrDescriptor):
    pass


class RailPDirMinusPoint(BaseAttrDescriptor):
    pass


class BorderPoint(BaseAttrDescriptor):
    pass


class BorderType(BaseAttrDescriptor):
    pass


class SectBorderPoints(BaseAttrDescriptor):
    pass


# ------------        IMAGE OBJECTS CLASSES        ------------ #


class StationObjectImage:
    attr_sequence_template = SOIAttrSeqTemplate()
    active_attrs = SOIActiveAttrs()
    dict_possible_values = SOIListPossibleValues()
    dict_values = SOIListValues()
    name = SOIName()


class CoordinateSystemSOI(StationObjectImage):
    cs_relative_to = CsCsRelTo("CoordinateSystemSOI")
    dependence = CsDepend(CEDependence(CEDependence.dependent))
    x = CsX("int")
    y = CsY("int")
    alpha = CsAlpha("int")
    co_x = CsCoX(CEBool(CEBool.true))
    co_y = CsCoY(CEBool(CEBool.true))


class AxisSOI(StationObjectImage):
    cs_relative_to = AxCsRelTo("CoordinateSystemSOI")
    creation_method = AxCrtMethod(CEAxisCreationMethod(CEAxisCreationMethod.translational))
    y = AxY("int")
    center_point = AxCenterPoint("PointSOI")
    alpha = AxAlpha("int")


class PointSOI(StationObjectImage):
    on = PntOn(CEAxisOrLine(CEAxisOrLine.axis))
    axis = PntAxis("AxisSOI")
    line = PntAxis("LineSOI")
    x = PntX("complex_type")


class LineSOI(StationObjectImage):
    points = LinePoints("complex_type")


class LightSOI(StationObjectImage):
    light_route_type = LightRouteType(CELightRouteType(CELightRouteType.train))
    light_stick_type = LightStickType(CELightStickType(CELightStickType.mast))
    center_point = LightCenterPoint("PointSOI")
    direct_point = LightDirectionPoint("PointSOI")
    colors = LightColors("complex_type")


class RailPointSOI(StationObjectImage):
    center_point = RailPCenterPoint("PointSOI")
    dir_plus_point = RailPDirPlusPoint("PointSOI")
    dir_minus_point = RailPDirMinusPoint("PointSOI")


class BorderSOI(StationObjectImage):
    border_type = BorderType(CEBorderType(CEBorderType.standoff))
    point = BorderPoint("PointSOI")


class SectionSOI(StationObjectImage):
    border_points = SectBorderPoints("complex_type")


# ------------        OTHER IMAGE CLASSES        ------------ #


class SOIEventHandler:
    pass


class SOIStorage:
    """ dumb class storage  """
    def __init__(self):
        self.class_objects: OrderedDict[str, OrderedDict[str, StationObjectImage]] = OrderedDict()
        for cls in StationObjectImage.__subclasses__():
            self.class_objects[cls.__name__] = OrderedDict()
        self.add_new_object(CoordinateSystemSOI(), GLOBAL_CS_NAME)

    def add_new_object(self, obj: StationObjectImage, name: str = None):
        if name:
            assert isinstance(obj, CoordinateSystemSOI) and (name == GLOBAL_CS_NAME), "Parameter only for GCS"
        else:
            name = obj.name
        self.class_objects[obj.__class__.__name__][name] = obj

    def get_object(self, name) -> StationObjectImage:
        for obj_dict in self.class_objects.values():
            if name in obj_dict:
                return obj_dict[name]
        assert False, "Name not found"

    @property
    def names_list(self) -> list[str]:
        nl = []
        for obj_dict in self.class_objects.values():
            nl.extend(obj_dict.keys())
        return nl


SOIS = SOIStorage()


class SOISelector:
    """ selected object editing """
    def __init__(self):
        self.current_object: Optional[StationObjectImage] = None
        self.is_new_object = True

    def create_empty_object(self, cls_name: str):
        assert cls_name in SOIS.class_objects, "Class name not found"
        cls: Type[StationObjectImage] = eval(cls_name)
        self.current_object: StationObjectImage = cls()
        self.is_new_object = True

    def edit_existing_object(self, obj_name: str):
        self.current_object = SOIS.get_object(obj_name)
        self.is_new_object = False

    def attrib_dict_possible_values(self):
        if not self.current_object:
            return OrderedDict()
        return self.current_object.dict_possible_values

    def attrib_dict_values(self):
        if not self.current_object:
            return OrderedDict()
        return self.current_object.dict_values


class ImageNameCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class SOIRectifier:
    """ objects sequence getter """
    def __init__(self):
        self.dg = OneComponentTwoSidedPG()  # dependence graph
        gcs_node = self.dg.insert_node()
        gcs_node.append_cell_obj(ImageNameCell(GLOBAL_CS_NAME))

    def build_dg(self, obj_list: list[StationObjectImage]) -> None:
        names_list: list[str] = [GLOBAL_CS_NAME]
        for obj in obj_list:
            if obj.name in names_list:
                raise ExistingNameCoError("Name {} already exist".format(obj.name))
            node = self.dg.insert_node()
            node.append_cell_obj(ImageNameCell(obj.name))
            names_list.append(obj.name)
        for obj in obj_list:
            for attr_name in obj.active_attrs:
                if not getattr(obj.__class__, attr_name).enum:
                    attr_value: str = getattr(obj, attr_name)
                    for name in names_list:
                        if name.isdigit():  # for rail points
                            continue
                        if " " in attr_value:
                            split_names = attr_value.split(" ")
                        else:
                            split_names = [attr_value]
                        for split_name in split_names:
                            if name == split_name:
                                node_self: PolarNode = single_element(lambda x: x.cell_objs[0].name == obj.name,
                                                                      self.dg.not_inf_nodes)
                                node_parent: PolarNode = single_element(lambda x: x.cell_objs[0].name == name,
                                                                        self.dg.not_inf_nodes)
                                self.dg.connect_inf_handling(node_self.ni_pu, node_parent.ni_nd)

    def check_cycle(self):
        dg = self.dg
        routes = dg.walk(dg.inf_pu.ni_nd)
        if any([route_.is_cycle for route_ in routes]):
            raise CycleError("Cycle in dependencies was found")

    def rectified_object_list(self) -> list[StationObjectImage]:
        return list(flatten(self.dg.longest_coverage()))[1:]


SOIR = SOIRectifier()


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
                if attr_name == "name":
                    setattr(new_obj, attr_name, attr_val)
                    continue
                if getattr(cls, attr_name).enum:
                    setattr(new_obj, attr_name, attr_val)
                else:
                    setattr(new_obj, attr_name, "_str_{}_str_".format(attr_val))
            objs_.append(new_obj)
    return objs_


def get_object_by_name(name, obj_list) -> StationObjectImage:
    for obj in obj_list:
        if obj.name == name:
            return obj
    assert False, "Name not found"

# -------------------------        MODEL CLASSES           -------------------- #


class ModelObject:
    pass


class CoordinateSystemMO(ModelObject):
    def __init__(self, base_cs: CoordinateSystemMO = None, co_x: bool = True, x: int = 0):
        self._base_cs = base_cs
        self._is_base = base_cs is None
        self._in_base_x = x
        self._in_base_co_x = co_x

    @property
    def is_base(self) -> bool:
        return self._is_base

    @property
    def base_cs(self) -> CoordinateSystemMO:
        if self.is_base:
            return self
        return self._base_cs

    @property
    def in_base_x(self) -> int:
        return self._in_base_x

    @property
    def in_base_co_x(self) -> bool:
        return self._in_base_co_x

    @property
    def absolute_x(self) -> int:
        if self.is_base:
            return self.in_base_x
        return self.base_cs.absolute_x + self.in_base_x

    @property
    def absolute_co_x(self) -> bool:
        if self.is_base:
            return self.in_base_co_x
        return self.base_cs.absolute_co_x == self.in_base_co_x


class MOStorage:
    def __init__(self):
        self.objects = []


GLOBAL_CS_MO = CoordinateSystemMO()


def build_model(images: list[StationObjectImage], current_object: StationObjectImage, file_read_mode: False):
    """ gets Images with str attribute values and builds model """
    names = OrderedDict()
    names[GLOBAL_CS_NAME] = GLOBAL_CS_MO

    """ names registration """
    for image in images:
        if not image.name:
            """ !!! ADD AUTO NAMING !!! """
            setattr(image, "_check_status_name", "Name for object not defined")
            return
        if image.name in names:
            setattr(image, "_check_status_name", "Name {} already exists".format(image.name))
            return
        names[image.name] = image

    """ attributes evaluation """
    for image in images:
        if isinstance(image, CoordinateSystemSOI):
            setattr(image, "_cs_relative_to", None)
            str_cs_relative_to = getattr(image, "_str_cs_relative_to")
            if not getattr(image, "_str_cs_relative_to"):
                setattr(image, "_predicted_cs_relative_to", GLOBAL_CS_NAME)
            else:
                if str_cs_relative_to not in names:
                    setattr(image, "_check_status_cs_relative_to", "CS {} not found".format(str_cs_relative_to))
                    return
                else:
                    cs_relative_to = names[str_cs_relative_to]
                    if not isinstance(cs_relative_to, CoordinateSystemSOI):
                        setattr(image, "_check_status_cs_relative_to", "Object {} is not CS".format(str_cs_relative_to))
                        return
                    setattr(image, "_cs_relative_to", names[str_cs_relative_to])


class ModelProcessor:
    def __init__(self):
        pass

    def predict_attributes(self, soi: StationObjectImage):
        pass


MODEL = ModelProcessor()


if __name__ == "__main__":
    test_1 = False
    if test_1:
        cs = CoordinateSystemSOI()
        print(cs.attr_sequence_template)
        print(cs.dependence)
        print(cs.active_attrs)
        cs.dependence = "independent"
        print()
        print(cs.active_attrs)
        cs.dependence = "dependent"
        print()
        print(cs.active_attrs)
        print(SOIS.class_objects)
        print(getattr(CsDepend, "__set__") == BaseAttrDescriptor.__set__)
        print(getattr(RailPDirMinusPoint, "__set__") == BaseAttrDescriptor.__set__)
        cs.cs_relative_to = "GlobalCS"
        cs.x = "35"
        cs.co_x = "false"

        for attr in cs.active_attrs:
            print(getattr(cs, attr))

        print(cs.dict_possible_values)
        print(cs.dict_values)

    test_2 = False
    if test_2:
        pnt = PointSOI()
        pnt.name = "Point"
        pnt.on = "line"
        SOIS.add_new_object(pnt)
        for attr in pnt.active_attrs:
            print(getattr(pnt, attr))
        ax = AxisSOI()
        ax.creation_method = "rotational"
        print()
        ax.center_point = "Point"
        for attr in ax.active_attrs:
            print(getattr(ax, attr))

    test_3 = False
    if test_3:
        pnt = PointSOI()
        pnt.x = "PK_12+34"
        print(type(pnt.x))
        print(pnt.x)
        print(PointSOI.attr_sequence_template)

    test_4 = False
    if test_4:
        cs = CoordinateSystemSOI()
        print(CoordinateSystemSOI.dict_possible_values)
        print(cs.dict_possible_values)

    test_5 = False
    if test_5:
        make_xlsx_templates(STATION_OUT_CONFIG_FOLDER)

    test_6 = True
    if test_6:
        objs = read_station_config(STATION_IN_CONFIG_FOLDER)
        pnt = get_object_by_name("Point_16", objs)
        # print(pnt.active_attrs)
        # for attr_ in pnt.active_attrs:
        #     print(getattr(pnt, attr_))
        SOIR.build_dg(objs)
        SOIR.check_cycle()
        # print(SOIR.dg.shortest_coverage())
        print(recursive_map(lambda x: x.cell_objs[0].name, SOIR.rectified_object_list()))
        # node_15: PolarNode = single_element(lambda x: x.cell_objs[0].name == "Point_15", SOIR.dg.not_inf_nodes)
        # node_4SP: PolarNode = single_element(lambda x: x.cell_objs[0].name == "4SP", SOIR.dg.not_inf_nodes)
        # node_6SP: PolarNode = single_element(lambda x: x.cell_objs[0].name == "6SP", SOIR.dg.not_inf_nodes)
        # print(node_15)
        # print(node_15.ni_nd.links)
        # print(node_4SP)
        # print(node_4SP.ni_pu.links)
        # print(node_6SP)
        # print(node_6SP.ni_pu.links)
        # print(len(SOIR.dg.walk(SOIR.dg.inf_pu.ni_nd)))
        # for route in SOIR.dg.walk(SOIR.dg.inf_pu.ni_nd):
        #     print(route.nodes)

    test_7 = False
    if test_7:
        pnt = PointSOI()
        pnt.x = "PK_12+34"
        print(pnt.x)
