import time
import numpy as np

def polyfit_test(_h):
    x = np.arange(len(_h))
    coef = np.polyfit(x, _h, 1)
    poly1d_fn = np.poly1d(coef)
    return poly1d_fn(x)

def manual_test(_h):
    x = np.arange(len(_h), dtype=float)
    n = len(_h)
    sum_x = np.sum(x)
    sum_y = np.sum(_h)
    sum_xy = np.sum(x * _h)
    sum_xx = np.sum(x * x)
    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0:
        return np.zeros_like(x)
    m = (n * sum_xy - sum_x * sum_y) / denominator
    b = (sum_y - m * sum_x) / n
    return m * x + b

arr = np.random.rand(50)

# warmup
for _ in range(100):
    polyfit_test(arr)
    manual_test(arr)

t0 = time.time()
for _ in range(10000):
    polyfit_test(arr)
t1 = time.time()

for _ in range(10000):
    manual_test(arr)
t2 = time.time()

print(f"polyfit: {t1-t0:.4f}s")
print(f"manual:  {t2-t1:.4f}s")
