## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.
## 2025-02-23 - Replaced np.polyfit with manual np.sum calculation
**Learning:** Using `np.polyfit` for 1D linear regression on small arrays incurs high overhead due to generalized routines (like SVD). Profiling showed a manual vectorized calculation using `np.sum` is much faster (over 3x speedup) for these small lists.
**Action:** Always prefer manual algebraic calculations in performance-critical loops when working with small 1D arrays, instead of relying on heavily generalized NumPy functions like `np.polyfit`.
