## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.
## 2024-05-24 - Optimization of `linearity` in `src/combine_postfits/utils.py`
**Learning:** Using `np.polyfit` for 1D linear regression on small arrays in tight loops incurs very high overhead because it uses generalized SVD routines.
**Action:** Replace `np.polyfit(x, y, 1)` with direct mathematical slope calculation `m = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean)**2)` which provides identical results but is ~3-4x faster. Ensure `x` is instantiated as `float` to avoid type issues.
