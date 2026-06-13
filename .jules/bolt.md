## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-05-18 - Manual linear regression vs np.polyfit
**Learning:** Using `np.polyfit` for 1D linear regression on small arrays incurs high overhead due to its generalized routines (e.g. SVD). Profiling showed it was a bottleneck when sorting samples by linearity.
**Action:** Replace `np.polyfit(x, y, 1)` with manual vectorized calculation of slope and intercept using `np.sum()`. This is significantly faster (~2.7x) and should be preferred in performance-critical loops when evaluating simple 1D linearity.
