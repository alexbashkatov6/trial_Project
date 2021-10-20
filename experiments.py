import time
start = time.time()
i = 1
for j in range(1000000):
    i *= j
finish = time.time()
print(finish-start)
