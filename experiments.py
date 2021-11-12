from functools import reduce
a = [{1, 2}, {2, 3}]
b = reduce(set.union, a)
print(b)

# set().union()
