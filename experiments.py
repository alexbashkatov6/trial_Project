from collections import OrderedDict

od = OrderedDict()
od[1] = 1
od[2] = 2
od[3] = 3
od.popitem()  # False
od = dict.fromkeys(['one', 'two', 'three', 'four'], 0)
print(od)
