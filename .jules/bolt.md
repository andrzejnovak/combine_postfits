## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Removed redundant O(N^2) list flattening over Uproot structures
**Learning:** Checking for keys across dictionaries via `set(sum([c.keys() for c in channels], []))` repeatedly creates intermediate lists and flattened structures, exhibiting O(N^2) time complexity. Using `sum(..., [])` to flatten arrays is an anti-pattern in Python.
**Action:** Replace list-flattening via `sum(..., [])` with set comprehensions `{k for c in channels for k in c.keys()}` and logical checks like `not any(...)` instead of full evaluation to get short-circuiting.
