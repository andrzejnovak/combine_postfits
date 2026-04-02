## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Fixed O(N^2) list flattening
**Learning:** The pattern `sum([list1, list2, ...], [])` is extremely inefficient in Python because it creates intermediate lists at every step, resulting in O(N^2) time complexity. This was heavily used when flattening matched channels from regex/glob filters.
**Action:** Use list comprehensions `[item for sublist in lists for item in sublist]` or `itertools.chain.from_iterable` instead to flatten lists linearly in O(N) time.

## 2025-02-19 - Short-circuiting boolean checks and generator optimizations
**Learning:** The expression `sum([p.is_alive() for p in _procs]) > 0` iterates over the entire list of processes, creates a new list, sums it, and then checks if the sum is positive.
**Action:** Using `any(p.is_alive() for p in _procs)` short-circuits the evaluation on the first alive process and avoids creating an intermediate list by using a generator expression, reducing both memory allocations and CPU cycles.
