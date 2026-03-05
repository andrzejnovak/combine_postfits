## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2026-03-05 - Optimize make_style_dict_yaml using directory-driven object extraction
**Learning:** `uproot` dictionary comprehensions that perform `file[f"dir/{key}"].to_hist()` inside nested loops for multiple metrics (like yield and linearity) are extremely slow due to redundant path string parsing, existence checks, and repeated `.to_hist()` array copying.
**Action:** Always fetch the `uproot` directory object once, iterate its `.keys()`, fetch the internal object once, convert `to_hist()` once, and compute all metrics simultaneously in a single pass. This avoids O(N) path-traversal and redundant memory allocations, reducing execution time by >60% on large files.
