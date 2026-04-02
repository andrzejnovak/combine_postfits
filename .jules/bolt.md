## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Avoided O(N^2) list flattening with sum()
**Learning:** In Python, flattening a list of lists using `sum([list_a, list_b], [])` is an O(N^2) anti-pattern because it repeatedly allocates and copies new lists on every addition. This was causing a bottleneck when aggregating keys from many Uproot directories. Set comprehensions (`{k for c in channels for k in c.keys()}`) or generators with `any()` are significantly faster (2.4x to ~100x improvement observed in benchmarks).
**Action:** Always avoid `sum(lists, [])`. Use list/set comprehensions for flattening, or `any()` when doing existence checks across multiple dictionaries/lists to benefit from short-circuiting.
