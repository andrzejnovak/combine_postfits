## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-05-01 - Fast Dictionary Membership Check
**Learning:** Flattening nested lists of dictionary keys via `sum(lists, [])` just to perform a boolean membership check incurs massive memory reallocation and O(N^2) time complexity.
**Action:** Use short-circuiting generator expressions with `any(key in dict for dict in list_of_dicts)` which is both faster and uses O(1) memory.
