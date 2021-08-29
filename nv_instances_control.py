import re


def instances_control(cls):
    cls.inst_count = 0
    cls.instances = set()
    cls.inst_names = set()

    def init_deco(init_fun):
        def new_init(*args, **kwargs):
            init_fun(*args, **kwargs)
            cls.inst_count += 1
            prefix = cls.__name__ + '_'
            autoname = prefix + str(cls.inst_count)
            if 'name' in kwargs:
                name_candidate = kwargs['name']
                assert type(name_candidate) == str, 'Name need be str'
                candidate_prefix = name_candidate[:name_candidate.index('_')]
                if candidate_prefix == prefix:
                    assert bool(re.fullmatch(r'\w+', name_candidate)), 'Name have to consists of alphas, nums and _'
                    assert name_candidate.startswith(prefix), 'Name have to begin from className_'
                    assert name_candidate != prefix, 'name cannot be == prefix; add specification to end'
                    assert not name_candidate[
                               len(prefix):].isdigit(), 'Not auto-name cannot be (prefix + int); choose other name'
                    assert not (name_candidate in cls.inst_names), 'Name repeating {}'.format(name_candidate)
                args[0].name = name_candidate
            else:
                args[0].name = autoname  # arg[0] = self
            cls.inst_names.add(args[0].name)
            cls.instances.add(args[0])

        return new_init
    cls.__init__ = init_deco(cls.__init__)
    return cls


if __name__ == '__main__':
    @instances_control
    class Probe:
        def __init__(self, *args, **kwargs):
            self.a = 1

    @instances_control
    class ProbeDeriv(Probe):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    @instances_control
    class ProbeDerivDeriv(ProbeDeriv):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
    p1 = Probe()
    p3 = Probe(name='Probe_mine')
    p4 = Probe(name='Probe_nb')
    print(p1.name)
    print(p3.name)
    print(p4.name)
    p2 = ProbeDeriv(name='ProbeDeriv_mine')
    p5 = ProbeDerivDeriv(name='ProbeDerivDeriv_mine')
    print(p2.name)
    print(Probe.inst_count)
    print(ProbeDeriv.inst_count)
    print(Probe.instances)
    print(Probe.inst_names)
    print(ProbeDeriv.instances)
    print(ProbeDeriv.inst_names)
