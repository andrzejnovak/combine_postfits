## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-23 - Removed O(N^2) list flattening
**Learning:** `sum([list1, list2], [])` is extremely inefficient in Python for flattening lists of lists. It creates intermediate lists at every step, making it O(N^2) memory and time.
**Action:** Always replace `sum([list_of_lists], [])` with a set/list comprehension like `[item for sublist in list_of_lists for item in sublist]` or `itertools.chain.from_iterable()`. Similarly, avoid `sum([list_comp])` when a generator expression `sum(gen_expr)` or short-circuiting `any(gen_expr)` can be used to skip the intermediate list allocation.
