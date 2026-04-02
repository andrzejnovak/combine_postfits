## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Removed overhead from generalized routines in `np.polyfit`
**Learning:** Using `np.polyfit` for 1D linear regression on small arrays (such as histogram bins) incurs high overhead due to generalized routines (like SVD). Manual vectorized calculation of slope and intercept using `np.sum` is approximately 3x faster and should be preferred in performance-critical loops like `linearity()` sorting.
**Action:** When performing simple mathematical operations like 1D linear regression on small datasets inside loops, implement the manual vectorized calculations via numpy rather than using high-level generalized functions to avoid massive overhead.
