from __future__ import annotations

from custom_enum import CustomEnum


class Color(CustomEnum):
    black = 0
    # other_black = 0
    white = 1
    red = 2
    yellow = 3
    green = 4
    blue = 5


class TextViewProperties:
    def __init__(self):
        self.font_type = None
        self.font_size = None
        self.font_style = None
        self.font_color = Color(Color.black)
        self.text_align = None


class BackgroundViewProperties:
    def __init__(self):
        self.color = Color(Color.white)


if __name__ == "__main__":
    c = Color("black")
    c2 = Color("black")
    c3 = Color("red")
    c4 = Color(Color.black)
    print(c == c2)
    print(c == "black")
    print(c == "other_black")
    print(c == Color.black)
    print(c == c3)
    print(c == "red")
    print(c == Color.red)
    print(Color.reversed_dict)
    print(c4.str_value)
    print(c4.are_in(["red", "blue"]))
