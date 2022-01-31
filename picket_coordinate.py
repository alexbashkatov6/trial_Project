class PicketCoordinateParsingCoError(Exception):
    pass


class PicketCoordinate:
    def __init__(self, str_value: str):
        self.str_value = str_value

    @property
    def value(self):
        x = self.str_value
        if x.startswith("PK"):
            try:
                hund_meters = x[x.index("_")+1:x.index("+")]
                meters = x[x.index("+"):]
                hund_meters = int(hund_meters)
                meters = int(meters)
            except ValueError:
                raise PicketCoordinateParsingCoError("Expected int value or picket 'PK_xx+xx'")
            return meters + 100*hund_meters
        else:
            try:
                meters = int(x)
            except ValueError:
                raise PicketCoordinateParsingCoError("Expected int value or picket 'PK_xx+xx'")
            return meters