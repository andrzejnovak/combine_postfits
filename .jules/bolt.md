## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2026-03-12 - Optimized make_style_dict_yaml performance with directory lookups and manual regression
**Learning:** `np.polyfit` is extremely slow for simple 1D arrays due to generalized routines (like SVD), and repeated path lookups in Uproot are expensive. `make_style_dict_yaml` called `to_hist()` multiple times on the same object, which is computationally expensive.
**Action:** Use manual vectorized linear regression for small 1D arrays. Always iterate over Uproot directories and cache `to_hist()` calls instead of performing full-path lookups and redundant conversions.
