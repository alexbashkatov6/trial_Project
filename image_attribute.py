from __future__ import annotations

from cell_object import CellObject
from view_properties import TextViewProperties, BackgroundViewProperties, Color


class ImageAttribute(CellObject):
    def __init__(self):
        super().__init__()
        self.name = None
        self.name_view_props = TextViewProperties()


class TitleAttribute(ImageAttribute):
    def __init__(self):
        super().__init__()


class SplitterAttribute(ImageAttribute):
    def __init__(self):
        super().__init__()
        self.possible_values: list[str] = []
        self.current_text = None

        self.text_view_props = TextViewProperties()


class FormAttribute(ImageAttribute):
    def __init__(self):
        super().__init__()
        self.current_text: str = ""
        self.requirement = None
        self.status_check: str = ""
        self.is_suggested: bool = False
        self.is_corrupted: bool = False

        self.text_view_props = TextViewProperties()
        self.background_props = BackgroundViewProperties()

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
