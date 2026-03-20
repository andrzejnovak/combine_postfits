## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-03-24 - Uproot Path Lookup Overhead
**Learning:** In Uproot, repeated full-path lookups (like `file['path/to/key']`) inside nested list comprehensions introduce severe redundant parsing and existence checks. Even extracting `fitDiag[f"shapes_{fit}/{ch}/{k}"].to_hist()` inside nested comprehensions multiplies the `.to_hist()` conversion cost by the number of metrics being calculated.
**Action:** When computing multiple metrics for objects in Uproot, always use a directory-driven approach. Iterate over available directories (`dir.keys()`), extract the object, call `.to_hist()` exactly once, and compute all necessary metrics simultaneously in a single pass.
