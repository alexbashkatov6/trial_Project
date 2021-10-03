from itertools import chain
a = {(1,2), (3,4)}
print({2,5} < set(chain(*a)))
# chain()