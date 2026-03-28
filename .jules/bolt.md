## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Replace np.polyfit with manual 1D linear regression
**Learning:** `np.polyfit` has significant overhead for small arrays due to its generalized routines (like SVD). Using it for 1D linear regression on histogram bins in a performance-critical sorting loop is slow.
**Action:** Replace `np.polyfit(x, y, 1)` with a manual, vectorized calculation of slope and intercept using `np.sum` to avoid the generalized overhead and execute ~3x faster.
