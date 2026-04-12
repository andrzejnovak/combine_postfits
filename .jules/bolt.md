## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2023-10-25 - np.polyfit overhead
**Learning:** `np.polyfit` has significant overhead due to generalized routines like SVD. For 1D linear regression on small arrays inside loops, manual calculation using the exact formulas with vectorized `np.sum` is much faster.
**Action:** Use manual calculation for 1D linear regression on small arrays.
