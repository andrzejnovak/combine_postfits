## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.
## 2026-06-06 - Replaced expensive list flattening for membership check with any()
**Learning:** Using `list(set(sum([c.keys() for c in channels], [])))` for a simple membership check is extremely inefficient (O(N^2) memory reallocation) and prevents short-circuiting. Profiling showed `any()` is significantly faster.
**Action:** Use short-circuiting `any()` instead of flattening nested lists for boolean membership checks.
