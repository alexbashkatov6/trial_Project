from __future__ import annotations

from custom_enum import CustomEnum
from cell_object import CellObject
from view_properties import TextViewProperties, BackgroundViewProperties, Color


class ImageAttribute(CellObject):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.name_view_props = TextViewProperties()


class TitleAttribute(ImageAttribute):
    def __init__(self, name):
        super().__init__(name)


class SplitterAttribute(ImageAttribute):
    def __init__(self, name, custom_enum: CustomEnum):
        super().__init__(name)
        self._enum = custom_enum

        self.text_view_props = TextViewProperties()

    @property
    def enum(self) -> CustomEnum:
        return self._enum

    @property
    def possible_values(self) -> list[str]:
        return self.enum.possible_values

    @property
    def current_text(self):
        return self.enum.str_value

    @current_text.setter
    def current_text(self, val):
        self._enum = type(self.enum)(val)

    @property
    def current_value(self):
        return self.enum.int_value


class VirtualSplitterAttribute(ImageAttribute):
    def __init__(self, name):
        super().__init__(name)
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value


class FormAttribute(ImageAttribute):
    def __init__(self, name, str_requirement: str = ""):
        super().__init__(name)
        self._current_text: str = ""
        self.last_valid_text: str = ""
        self.str_requirement = str_requirement
        self.status_check: str = ""
        self.is_suggested: bool = False
        self.is_corrupted: bool = False

        self.text_view_props = TextViewProperties()
        self.background_props = BackgroundViewProperties()

    @property
    def current_text(self):
        return self._current_text

    @current_text.setter
    def current_text(self, val):
        self._current_text = val

    def select_background_color(self):
        if not self.current_text or self.current_text.isspace():
            self.background_props.color = Color(Color.white)
        elif self.status_check and not self.status_check.isspace():
            self.background_props.color = Color(Color.red)
        elif self.is_suggested:
            self.background_props.color = Color(Color.yellow)
        else:
            self.background_props.color = Color(Color.green)

    def select_text_color(self):
        if self.is_corrupted:
            self.text_view_props.font_color = Color(Color.red)
        else:
            self.text_view_props.font_color = Color(Color.black)


if __name__ == "__main__":
    title_attr = TitleAttribute("Title")
    print(title_attr.name)

    class SampleEnum(CustomEnum):
        first = 0
        second = 1

    split_attr = SplitterAttribute("Split", SampleEnum("first"))
    print(split_attr.name)
    print(split_attr.possible_values)
    print(split_attr.current_text)
