from sm_attrib_cell import ComplexAttrib, AttribGroup, CompetitorAttribGroup


class AttribsContainer:
    def __init__(self):
        self.attrDict = {'CoordinateSystem': [],
                         'Point': [],
                         'Line': [],
                         'GroundLine': []}
        ca1_CS = ComplexAttrib('Name', 'str')
        crag1_CS = CompetitorAttribGroup('Creation method')
        ag1_CS = AttribGroup('Create basis')
        crag1_CS.addGroup(ag1_CS)
        ag2_CS = AttribGroup('Relative to CS')
        crag1_CS.addGroup(ag2_CS)
        ca1_ag2_CS = ComplexAttrib('Relative CS name', 'CoordinateSystem')
        ag2_CS.addAttrib(ca1_ag2_CS)
        ca2_ag2_CS = ComplexAttrib('Relative position', 'float')
        ag2_CS.addAttrib(ca2_ag2_CS)
        ca3_ag2_CS = ComplexAttrib('Is co-direct', [-1, 1])
        ag2_CS.addAttrib(ca3_ag2_CS)
        self.attrDict['CoordinateSystem'].append(ca1_CS)
        self.attrDict['CoordinateSystem'].append(crag1_CS)


Ac = AttribsContainer()
