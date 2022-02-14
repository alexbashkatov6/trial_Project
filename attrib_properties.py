from dataclasses import dataclass


@dataclass
class AttribProperties:
    name: str = ""
    suggested_value: str = ""
    last_input_value: str = ""
    last_confirmed_value: str = ""

    is_required: str = ""
    count_requirement: str = ""
    is_min_count: str = ""
    check_status: str = ""
