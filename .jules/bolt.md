## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-05-28 - Optimize metrics computation in make_style_dict_yaml
**Learning:** Computing metrics like yield and linearity using key-driven, top-down path lookups (`file['path/to/key'].to_hist()`) is extremely slow for large ROOT files. Converting Uproot objects to histograms via `to_hist()` is computationally expensive, especially when done redundantly.
**Action:** Use a directory-driven pattern: iterate through available Uproot directories (`file['path/to/dir']`), parse valid sample keys from `dir_obj.keys()`, extract objects via `dir_obj[key]`, call `.to_hist()` exactly once, and compute all metrics (yield, linearity) simultaneously in a single pass.
