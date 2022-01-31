from typing import Optional, Iterable, Type

from two_sided_graph import Element
from cell_object import CellObject
from extended_itertools import single_element, EINotFoundError, EIManyFoundError


class CellError(Exception):
    pass


class NotFoundCellError(CellError):
    pass


class ManyFoundCellError(CellError):
    pass


def element_cell_by_type(el: Element, cls: Type) -> CellObject:
    # cls = eval(cls_name)
    found_cells = set()
    for cell in el.cell_objs:
        if isinstance(cell, cls):
            found_cells.add(cell)
    if not found_cells:
        raise NotFoundCellError("Not found")
    if len(found_cells) != 1:
        raise ManyFoundCellError("More then 1 cell found")
    return found_cells.pop()


def all_cells_of_type(elements: Iterable[Element], cls: Type) -> dict[CellObject, Element]:
    result = {}
    for element in elements:
        try:
            co = element_cell_by_type(element, cls)
        except CellError:
            continue
        result[co] = element
    return result


def find_cell_name(elements: Iterable[Element], cls: Type, name: str) -> Optional[tuple[CellObject, Element]]:
    cell_candidates = all_cells_of_type(elements, cls)
    try:
        co = single_element(lambda x: x.name == name, list(cell_candidates.keys()))
    except EINotFoundError:
        raise NotFoundCellError("Not found")
    except EIManyFoundError:
        raise ManyFoundCellError("More then 1 cell found")
    return co, cell_candidates[co]
