## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Removed np.polyfit overhead for small array 1D linear regression
**Learning:** `np.polyfit(..., 1)` is extremely slow for 1D linear regressions on small arrays (like histogram bins) because it uses generalized Singular Value Decomposition (SVD) under the hood. For small data sets, this overhead is massive (~3x slower).
**Action:** When performing 1D linear regressions on small arrays in performance-sensitive paths (like sample sorting based on linearity over many distributions), replace `np.polyfit` with manual Exact Ordinary Least Squares calculation using `np.sum()`. Use `np.errstate` to handle zero-divisions instead of relying on slow exception blocks.
