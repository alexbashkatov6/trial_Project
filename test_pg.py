from nv_polar_graph import PolarGraph # , PGMoves

pg_1 = PolarGraph()
pg_2 = PolarGraph()
pg_3 = PolarGraph()
pg_4 = PolarGraph()
pg_5 = PolarGraph()
pg_1.moves_group.group_policy = 'one_of'
pg_1.connect_external_to_its_end(pg_2, end='nd')
pg_1.connect_external_to_its_end(pg_4)
pg_3.connect_external_to_its_end(pg_1)
pg_5.connect_external_to_its_end(pg_1)

print('pg_1 = ', pg_1)
print('pg_2 = ', pg_2)
print('pg_1 negative = ', pg_1.links_negative_down)
print('pg_1 positive = ', pg_1.links_positive_up)
print('pg_2 negative = ', pg_2.links_negative_down)
print('pg_2 positive = ', pg_2.links_positive_up)

for link in pg_1.links_negative_down:
    print('link', link.ends)

pg_1.content['default'] = 6
pg_1.content['custom_content'] = pg_3
print('pg_1.content = ', pg_1.content.keys())
print('pg_1.content = ', pg_1.content['default'], pg_1.content['custom_content'])
print('pg_2.content = ', pg_2.content)

# print('pg_1.content.is_complex = ', pg_1.content.is_complex())
# print('pg_2.content.is_complex = ', pg_2.content.is_complex())

print('moves pg_1 = ', pg_1.moves_group.moves)
print('moves pg_2 = ', pg_2.moves_group.moves)
print('moves pg_3 = ', pg_3.moves_group.moves)

for move in pg_1.moves_group.moves:
    print('pg_1 moves = ', move.active)

# m_1 = PGMoves()
# m_1.moves_activity = {'first move': False, 'second move': False, 'third move': False}
# print(m_1.active_moves, m_1.inactive_moves)



