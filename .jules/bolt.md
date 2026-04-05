## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.
## 2024-05-15 - Fast 1D Linear Regression
**Learning:** `np.polyfit` incurs high overhead for simple 1D linear regression on small arrays (like histogram bins) because it uses generalized SVD routines.
**Action:** When calculating 1D linearity in hot loops (e.g. sorting histograms), use manual vectorized calculations of slope and intercept via `np.sum` to achieve ~3x faster performance.
