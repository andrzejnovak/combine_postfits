## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Fast Iteration & Membership checks
**Learning:** `sum([c.keys() for c in channels], [])` behaves as an O(N^2) operation because it continually reallocates lists. Additionally, flattening a structure just to test membership for a single element is wasteful. Using a generator with `any(key in collection)` gives a dramatic speedup due to short-circuit evaluation.
**Action:** Always favor set comprehensions (like `{k for c in channels for k in c.keys()}`) over `sum()` flattening for collections. Whenever testing existence across multiple dictionaries or items, prioritize `any()` with generators to avoid building temporary full structures.
