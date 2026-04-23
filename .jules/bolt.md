## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Replace explicit summations inside loop tracking with `any` short-circuit checks.
**Learning:** `sum([p.is_alive() for p in _procs])` loops strictly bounded O(N) allocation and summation in checking processes inside a long running while block. Use `any(p.is_alive() for p in _procs)` to use python generator behavior for quick O(1) performance inside infinite tracking loops.
**Action:** Identify and replace existence checks that explicitly generate new lists or calculate strict integer summations in `while` loops for simple tracking purposes.
