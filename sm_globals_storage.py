class SmGlobals:
    @staticmethod
    def add(x, val=None):
        assert type(x) == str, 'str need'
        globals()[x] = val

    @staticmethod
    def get(x):
        return globals()[x]

    @staticmethod
    def pop(x):
        globals().pop(x)

    @staticmethod
    def eval(x):
        assert type(x) == str, 'str need'
        return eval(x)

