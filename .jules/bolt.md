## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-05-07 - Avoid np.polyfit for 1D arrays
**Learning:** Using `np.polyfit` for 1D linear regression on small arrays incurs high overhead due to generalized routines (like SVD). Manual vectorized calculation of slope and intercept using `np.sum` is significantly faster (~5.7x) and should be preferred in performance-critical loops.
**Action:** When calculating simple linear regression lines in performance-critical paths, use manual vectorized numpy operations instead of `np.polyfit`. Ensure the independent variable array is instantiated as a float (e.g., `np.arange(n, dtype=float)`) to avoid integer division or precision issues.
