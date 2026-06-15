## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-05-18 - Replace `sum([list], [])` with short-circuiting `any()`
**Learning:** Checking for the presence of a key across a list of dictionaries via flattening `sum([c.keys() for c in channels], [])` creates an intermediate O(N^2) list and performs an O(N) set conversion. In hot loops or large dictionaries, this introduces significant overhead (up to ~140x slower than the optimal approach).
**Action:** When only a boolean membership check is needed, always replace list flattening with a generator expression and the short-circuiting `any()` function, like `any("key" in d for d in list_of_dicts)`.
