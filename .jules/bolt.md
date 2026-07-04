## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Replaced `np.polyfit` with manual vectorized calculation
**Learning:** Using `np.polyfit` for 1D linear regression on small arrays incurs high overhead due to generalized routines (like SVD). Manual vectorized calculation of slope and intercept using `np.sum` is significantly faster (~3.2x to ~5.7x) and should be preferred in performance-critical loops. Ensure the independent variable array is instantiated as a float to avoid integer division or precision issues.
**Action:** When performing simple 1D linear regression (degree 1) in a loop, avoid `np.polyfit`. Instead, calculate slope and intercept manually using standard least squares equations (`np.sum` operations).
