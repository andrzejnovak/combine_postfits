## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.
## 2025-02-19 - Replace np.polyfit with manual calculation
**Learning:** `np.polyfit` on small arrays incurs high generalized SVD overhead. For simple 1D linear regression, direct vectorized operations using `.sum()` are much faster.
**Action:** Use manual slope/intercept calculations for small arrays instead of generalized regression tools when speed is critical.
