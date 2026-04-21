## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.
## 2024-04-21 - [np.polyfit vs manual regression on small arrays]
**Learning:** `np.polyfit` uses generalized routines (like SVD) which incur significant overhead. On small 1D arrays, manual vectorized linear regression using `np.sum` is approximately 3x faster.
**Action:** Replace `np.polyfit` with manual regression logic when calculating slopes and intercepts for small arrays in performance-critical loops. Ensure independent variables are initialized as floats to prevent integer division artifacts.
