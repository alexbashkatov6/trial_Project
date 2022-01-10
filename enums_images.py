from custom_enum import CustomEnum


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


class CELightType(CustomEnum):
    train = 0
    shunt = 1


class CELightColor(CustomEnum):
    red = 0
    blue = 1
    white = 2
    yellow = 3
    green = 4


class CEBorderType(CustomEnum):
    standoff = 0
    ab = 1
    pab = 2