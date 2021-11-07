class CycleError(Exception):
    pass


class CellError(Exception):
    pass


class TypeCellError(CellError):
    pass


class SyntaxCellError(CellError):
    pass


class SemanticCellError(CellError):
    pass


class CycleCellError(CellError):
    pass
