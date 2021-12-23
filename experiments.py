
def apply_filter(f, objs):
    out_type = type(objs)
    return out_type(filter(f, objs))

def f_default(val):
    return val>2

print(apply_filter(f_default, {1,2,3}))
