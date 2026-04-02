## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-04-02 - Flattening Lists
**Learning:** Using `sum([lists], [])` to flatten nested collections (e.g. `sum([c.keys() for c in channels], [])`) executes in O(N^2) time by repeatedly allocating memory. Using this flattened collection just to check for key existence (e.g., `"total_signal" in flattened_list`) wastes CPU cycles, as it fully evaluates instead of short-circuiting.
**Action:** Replace `sum([lists], [])` with set comprehensions `{k for c in channels for k in c.keys()}` or `itertools.chain.from_iterable` for flattening. Replace existence checks on flattened lists with `any(key in c for c in channels)` to leverage short-circuiting.
