from polar_graph import PolarGraph

pg_1 = PolarGraph()
pg_2 = PolarGraph()
pg_3 = PolarGraph()
pg_1.pg_connect(pg_2)

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

print('pg_1.content.is_complex = ', pg_1.content.is_complex())
print('pg_2.content.is_complex = ', pg_2.content.is_complex())
print()
