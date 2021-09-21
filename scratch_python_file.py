import inspect


class CoordSystem:
    def __init__(self, x: int = None, y: int = None, alpha: int = None, co_X: int = None, co_Y: int = None):
        self.x = x
        self.y = y
        self.alpha = alpha
        self.co_X = co_X
        self.co_Y = co_Y


GCS = CoordSystem()


class IndependentBasis(CoordSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.basis = GCS


class DependentBasis(CoordSystem):
    def __init__(self, basis: CoordSystem = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.basis = basis


arg_spec = inspect.getfullargspec(DependentBasis.__init__)
print('arg_spec', arg_spec)
print('mro', DependentBasis.mro())
print('annotations', DependentBasis.__init__.__annotations__)
