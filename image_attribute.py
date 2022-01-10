from __future__ import annotations
from collections.abc import Iterable

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
    def __init__(self, name, custom_enum: CustomEnum, excepted_values: Iterable[str] = None,
                 with_default: bool = False):
        super().__init__(name)
        self._base_enum = custom_enum
        if not excepted_values:
            self.excepted_values = []
        else:
            self.excepted_values = excepted_values
        self.with_default = with_default
        self._current_text = None

        self.text_view_props = TextViewProperties()

    @property
    def base_enum(self) -> CustomEnum:
        return self._base_enum

    @property
    def possible_values(self) -> list[str]:
        p_values = self.base_enum.possible_values
        if self.with_default:
            p_values.append("no_value")
        return [p_value for p_value in p_values if p_value not in self.excepted_values]

    @property
    def excepted_values(self):
        return self._excepted_values

    @excepted_values.setter
    def excepted_values(self, val: Iterable[str]):
        self._excepted_values = list(val)

    @property
    def with_default(self):
        return self._with_default

    @with_default.setter
    def with_default(self, val: bool):
        self._with_default = val

    @property
    def current_text(self):
        return self._current_text

    @current_text.setter
    def current_text(self, val: str):
        if val != "no_value":
            self._base_enum = type(self.base_enum)(val)
        self._current_text = val

    @property
    def current_value(self) -> int:
        if self._current_text == "no_value":
            return -1
        return self.base_enum.int_value


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
