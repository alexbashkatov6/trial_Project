from nv_polar_graph import BasePolarGraph, PolarNode, PGMove
from nv_associations import AttribNodeAssociation, AttribMoveAssociation

pg_0 = BasePolarGraph()
assoc = pg_0.am
pn_1, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pg_0.inf_node_nd.ni_pu)
pn_2, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
pn_3, _, _ = pg_0.insert_node_single_link(pg_0.inf_node_pu.ni_nd, pn_1.ni_pu)
pn_4, link_1, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
pn_5, _, _ = pg_0.insert_node_single_link(pn_1.ni_nd, pg_0.inf_node_nd.ni_pu)
assoc.node_assoc_class = AttribNodeAssociation
assoc.move_assoc_class = AttribMoveAssociation
# assoc.add_to_curr_context(PolarNode, 'attrib_node')
assoc.auto_set_curr_context()
# def f(x):
#     return x.name
# assoc.find_function = f
cell_1 = assoc.create_cell(pn_1, 'Cell_1', 'str')
cell_2 = assoc.create_cell(pn_2, 'Cell_2', 'str')
cell_3 = assoc.create_cell(pn_3, 'Cell_3', 'str')
cell_4 = assoc.create_cell(pn_4, 'Cell_4', 'str')
cell_5 = assoc.create_cell(pn_5, 'Cell_5', 'str')
pn_1: PolarNode
move_1 = pn_1.ni_nd.get_move(link_1)
cell_move_1 = assoc.create_cell(move_1, 'Cell_move_1', 'str')
# print(cell_move_1)
# print(assoc.curr_context)
# print(assoc.get_elm_cell_by_context(pn_1, 'attrib_node'))
# print(assoc.get_single_elm_by_cell_content(PolarNode, 'Cell_3'))
# print(assoc.get_single_elm_by_cell_content(PGMove, 'Cell_move_1'))
# print(cell_1.__dict__)
assoc.apply_sbg_content(PolarNode, 'nanana')
print(cell_1.__dict__)
# print(assoc.cells)

route = pg_0.find_single_route(pn_2, pn_4)
rc = assoc.extract_route_content(route)
print(rc)
for cell in rc:
    print(cell.pop().name)
