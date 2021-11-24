from abc import ABC, abstractmethod

class A(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def seter(self):
        pass

class B(A):
    pass

a = B()
a.seter()