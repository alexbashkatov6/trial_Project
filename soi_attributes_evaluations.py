from collections import OrderedDict, Counter

from soi_objects import BaseAttrDescriptor, StationObjectImage, CoordinateSystemSOI, AxisSOI, PointSOI, LineSOI, \
    LightSOI, RailPointSOI, BorderSOI, SectionSOI
from picket_coordinate import PicketCoordinate
from enums_images import CELightColor


class AttributeEvaluateError(Exception):
    pass


class AEPreSemanticError(AttributeEvaluateError):
    pass


class AERequiredAttributeError(AttributeEvaluateError):
    pass


class AEObjectNotFoundError(AttributeEvaluateError):
    pass


class AETypeAttributeError(AttributeEvaluateError):
    pass


def check_expected_type(str_value: str, attr_name: str, image_object: StationObjectImage, names_dict: OrderedDict):
    attr_descr: BaseAttrDescriptor = getattr(image_object.__class__, attr_name)
    if issubclass(attr_descr.expected_type, StationObjectImage):
        if str_value not in names_dict:
            raise AEObjectNotFoundError(attr_name, "Object {} not found".format(str_value))
        rel_image = names_dict[str_value]
        if not isinstance(rel_image, attr_descr.expected_type):
            raise AETypeAttributeError(attr_name,
                                       "Object {} not satisfy required type {}".format(str_value,
                                                                                       attr_descr.str_expected_type))
        setattr(image_object, "_{}".format(attr_name), names_dict[str_value])
    else:
        try:
            result = eval(str_value)
        except (ValueError, NameError, SyntaxError):
            raise AETypeAttributeError(attr_name,
                                       "Object {} not satisfy required type {}".format(str_value,
                                                                                       attr_descr.str_expected_type))
        if not isinstance(result, attr_descr.expected_type):
            raise AETypeAttributeError(attr_name,
                                       "Object {} not satisfy required type {}".format(str_value,
                                                                                       attr_descr.str_expected_type))
        setattr(image_object, "_{}".format(attr_name), result)


def default_attrib_evaluation(attr_name: str, image: StationObjectImage, names_dict: OrderedDict):
    if attr_name in image.active_attrs:
        setattr(image, "_{}".format(attr_name), None)
        str_attr_value = getattr(image, "_str_{}".format(attr_name))
        if not getattr(image, "_str_{}".format(attr_name)):
            raise AERequiredAttributeError(attr_name, "Attribute {} required".format(attr_name))
        else:
            check_expected_type(str_attr_value, attr_name, image, names_dict)


def evaluate_attributes(names_soi: OrderedDict[str, StationObjectImage], rect_so: list[str]) -> \
        OrderedDict[str, StationObjectImage]:
    for image_name in rect_so:
        image = names_soi[image_name]

        if isinstance(image, CoordinateSystemSOI):
            default_attrib_evaluation("cs_relative_to", image, names_soi)
            default_attrib_evaluation("x", image, names_soi)

        if isinstance(image, AxisSOI):
            default_attrib_evaluation("cs_relative_to", image, names_soi)
            default_attrib_evaluation("y", image, names_soi)
            default_attrib_evaluation("center_point", image, names_soi)
            default_attrib_evaluation("alpha", image, names_soi)

        if isinstance(image, PointSOI):
            default_attrib_evaluation("axis", image, names_soi)
            default_attrib_evaluation("line", image, names_soi)
            default_attrib_evaluation("cs_relative_to", image, names_soi)
            attr_name = "x"
            if attr_name in image.active_attrs:
                setattr(image, "_{}".format(attr_name), None)
                str_attr_value = getattr(image, "_str_{}".format(attr_name))
                if not getattr(image, "_str_{}".format(attr_name)):
                    raise AERequiredAttributeError(attr_name, "Attribute {} required".format(attr_name))
                else:
                    setattr(image, "_{}".format(attr_name), PicketCoordinate(str_attr_value).value)

        if isinstance(image, LineSOI):
            attr_name = "points"
            if attr_name in image.active_attrs:
                setattr(image, "_{}".format(attr_name), None)
                str_attr_value: str = getattr(image, "_str_{}".format(attr_name))
                if not getattr(image, "_str_{}".format(attr_name)):
                    raise AERequiredAttributeError(attr_name, "Attribute {} required".format(attr_name))
                else:
                    str_points = str_attr_value.split(" ")
                    if len(str_points) < 2:
                        raise AEPreSemanticError(attr_name, "Count of points should be 2, given count <2")
                    if len(str_points) > 2:
                        raise AEPreSemanticError(attr_name, "Count of points should be 2, given count >2")
                    str_points: list[str]
                    if str_points[0] == str_points[1]:
                        raise AEPreSemanticError(attr_name, "Given points are equal, cannot build line")
                    pnts_list = []
                    for str_value in str_points:
                        if str_value not in names_soi:
                            raise AEObjectNotFoundError(attr_name, "Object {} not found".format(str_value))
                        rel_image = names_soi[str_value]
                        if not isinstance(rel_image, PointSOI):
                            raise AETypeAttributeError(attr_name, "Object {} not satisfy required type {}"
                                                       .format(str_value, "PointSOI"))
                        pnts_list.append(rel_image)
                    setattr(image, "_{}".format(attr_name), pnts_list)

        if isinstance(image, LightSOI):
            default_attrib_evaluation("center_point", image, names_soi)
            default_attrib_evaluation("direct_point", image, names_soi)
            attr_name = "colors"
            if attr_name in image.active_attrs:
                setattr(image, "_{}".format(attr_name), None)
                str_attr_value: str = getattr(image, "_str_{}".format(attr_name))
                if not getattr(image, "_str_{}".format(attr_name)):
                    raise AERequiredAttributeError(attr_name, "Attribute {} required".format(attr_name))
                else:
                    str_colors = str_attr_value.split(" ")
                    color_counts = dict(Counter(str_colors))
                    for str_color in color_counts:
                        if str_color not in CELightColor.possible_values:
                            raise AETypeAttributeError(attr_name, "Color {} for light not possible".format(str_color))
                        if color_counts[str_color] > 1 and str_color != "yellow":
                            raise AETypeAttributeError(attr_name,
                                                       "More then 2 lamps for color {} not possible".format(str_color))
                    setattr(image, "_{}".format(attr_name), str_colors)

        if isinstance(image, RailPointSOI):
            default_attrib_evaluation("center_point", image, names_soi)
            default_attrib_evaluation("dir_plus_point", image, names_soi)
            default_attrib_evaluation("dir_minus_point", image, names_soi)

        if isinstance(image, BorderSOI):
            default_attrib_evaluation("point", image, names_soi)

        if isinstance(image, SectionSOI):
            attr_name = "border_points"
            if attr_name in image.active_attrs:
                setattr(image, "_{}".format(attr_name), None)
                str_attr_value: str = getattr(image, "_str_{}".format(attr_name))
                if not getattr(image, "_str_{}".format(attr_name)):
                    raise AERequiredAttributeError(attr_name, "Attribute {} required".format(attr_name))
                else:
                    str_points = str_attr_value.split(" ")
                    if len(set(str_points)) < len(str_points):
                        raise AEPreSemanticError(attr_name, "Points in section border repeating")
                    pnts_list = []
                    for str_value in str_points:
                        if str_value not in names_soi:
                            raise AEObjectNotFoundError(attr_name, "Object {} not found".format(str_value))
                        rel_image = names_soi[str_value]
                        if not isinstance(rel_image, PointSOI):
                            raise AETypeAttributeError(attr_name, "Object {} not satisfy required type {}"
                                                       .format(str_value, "PointSOI"))
                        pnts_list.append(rel_image)
                    setattr(image, "_{}".format(attr_name), pnts_list)

    return names_soi
