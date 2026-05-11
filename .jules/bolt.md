## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Replaced np.polyfit with manual vectorized linear regression
**Learning:** `np.polyfit` incurs significant overhead for 1D linear regression on small arrays due to generalized routines (like SVD). Profiling showed that it is ~5.7x slower than calculating slope and intercept directly using `np.sum`.
**Action:** Use manual vectorized calculation of slope and intercept (ensuring independent variable is float) instead of `np.polyfit` in performance-critical loops operating on small arrays.
