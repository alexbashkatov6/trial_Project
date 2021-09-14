import re


def names_control(cls):
    cls._inst_count = 0
    # cls.instances = set()
    # cls.inst_names = set()
    cls._names_to_instances = {}

    def get_inst_by_name(clss, name: str):
        return clss._names_to_instances[name]

    def get_instances(clss):
        return list(clss._names_to_instances.values())

    def init_deco(init_fun):
        def new_init(*args, **kwargs):
            name_candidate = ''
            if 'name' in kwargs:
                name_candidate = kwargs.pop('name')
            init_fun(*args, **kwargs)
            if type(args[0]) == cls:  # arg[0] = self
                cls._inst_count += 1
                prefix = cls.__name__ + '_'
                autoname = prefix + str(cls._inst_count)
                if name_candidate:
                    assert type(name_candidate) == str, 'Name need be str'
                    assert bool(re.fullmatch(r'\w+', name_candidate)), 'Name have to consists of alphas, nums and _'
                    assert name_candidate.startswith(prefix), 'Name have to begin from className_'
                    assert name_candidate != prefix, 'name cannot be == prefix; add specification to end'
                    assert not name_candidate[
                               len(prefix):].isdigit(), 'Not auto-name cannot be (prefix + int); choose other name'
                    assert not (name_candidate in cls._names_to_instances.keys()), 'Name repeating {}'.format(name_candidate)
                    args[0].name = name_candidate
                else:
                    args[0].name = autoname
                cls._names_to_instances[args[0].name] = args[0]
                # cls.inst_names.add(args[0].name)
                # cls.instances.add(args[0])
        return new_init

    def repr_deco(repr_fun):
        def new_repr(*args, **kwargs):
            old_repr = repr_fun(*args, **kwargs)
            if '{} object at'.format(args[0].__class__.__name__) in old_repr:
                # cleared_old_repr = old_repr[old_repr.find('<'):old_repr.rfind('>') + 1]
                # return '{} ({})'.format(args[0].name, cleared_old_repr)
                return args[0].name
            else:
                return old_repr
        return new_repr

    cls.__init__ = init_deco(cls.__init__)
    cls.__repr__ = repr_deco(cls.__repr__)
    # assert not hasattr(cls, 'get_inst_by_name'), 'Function get_inst_by_name overload'
    cls.get_inst_by_name = classmethod(get_inst_by_name)
    cls.get_instances = classmethod(get_instances)
    # if not
    return cls


if __name__ == '__main__':

    @names_control
    class Probe:
        def __init__(self): #
            self.a = 1

    @names_control
    class ProbeDeriv(Probe):
        def __init__(self):
            super().__init__()

    @names_control
    class ProbeDerivDeriv(ProbeDeriv):
        def __init__(self, a=0):
            super().__init__()

    p1 = Probe()
    p3 = Probe(name='Probe_mine')
    p4 = Probe(name='Probe_nb')
    print(p1.name)
    print(p3.name)
    print(p4.name)
    p2 = ProbeDeriv(name='ProbeDeriv_mine')
    p5 = ProbeDerivDeriv(name='ProbeDerivDeriv_mine')
    print('implicit type = ', type(p5) == Probe, type(p5) == ProbeDeriv, type(p5) == ProbeDerivDeriv)
    print('get inst = ', Probe.get_inst_by_name('Probe_mine'),
          ProbeDeriv.get_inst_by_name('ProbeDeriv_mine'),
          ProbeDerivDeriv.get_inst_by_name('ProbeDerivDeriv_mine'))
    # print('hasattr repr = ', hasattr(Probe, '__repr__'), dir(Probe))
    print(p2.name)
    # print(Probe._inst_count)
    # print(ProbeDeriv._inst_count)
    # print(ProbeDerivDeriv._inst_count)
    # print(Probe.instances)
    # print(Probe.inst_names)
    # print(ProbeDeriv.instances)
    # print(ProbeDeriv.inst_names)
    print(Probe._names_to_instances['Probe_mine'])
    print(Probe.get_instances())

    print([1,2,3]+[3, 5, 6])
    print({1, 2, 3} & {3, 5, 6})
    a = {1, 2, 3}
    a |= {5, 6}
    print('a = ', a)

    b = {1:{1,2,3}, 2:{4,5,6}}
    b[1].pop()
    print(b)

    c = [1]
    c.pop(-1)
    print(c)

    # d = {1:'1', 2:'2'}
    # d.pop(6)
    # print(d)

    # class Base:
    #     def __init__(self, cls_name: str, params_dict: dict[str, int]):
    #         type(cls_name, (self.__class__,), params_dict)
    #
    # subclass = Base('sbcl', {'par_1': 1})
    # print(subclass)
    # print(subclass.par_1)
    # from collections import namedtuple
    # a = namedtuple('a', ['ab', 'cd'])
    # print(a)

    # def class_gen(cls_name: str, )

