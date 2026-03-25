## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Fast short-circuiting with any()
**Learning:** Checking for the existence of active multiprocessing processes using `sum([p.is_alive() for p in _procs]) > 0` iterates over all processes and allocates a list, every loop iteration. Replacing it with `any(p.is_alive() for p in _procs)` takes advantage of short-circuiting, immediately returning `True` upon finding the first living process without evaluating the rest, saving CPU cycles.
**Action:** When evaluating if at least one item in a collection meets a condition, prefer `any(generator_expression)` over `sum() > 0` or `len() > 0` to leverage early exit.
