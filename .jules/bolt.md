## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-05-19 - Avoid `np.polyfit` for small 1D linear regressions
**Learning:** `np.polyfit` has high overhead for simple 1D linear regressions on small arrays because it utilizes generalized routines (like SVD). For the `linearity` calculation in `make_style_dict_yaml`, which runs inside a nested loop over many small arrays, this causes a significant performance bottleneck.
**Action:** Replace `np.polyfit` with manual vectorized calculations of slope and intercept using `np.sum()`. Ensure the independent variable array is instantiated as float (`np.arange(n, dtype=float)`) to avoid precision issues. This yields a >3x speedup.
