## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-05-24 - Replace np.polyfit for small array linear regression
**Learning:** `np.polyfit` uses generalized SVD routines which incur significant overhead when fitting 1D lines to very small arrays (e.g. 5-10 bins common in HEP distributions).
**Action:** Replace `np.polyfit(x, y, 1)` with manual vectorized calculation of slope and intercept using `np.sum()` for an O(1) mathematical speedup.
