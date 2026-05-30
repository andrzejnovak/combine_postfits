## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Replace np.polyfit with explicit mathematical calculations for 1D linear regressions
**Learning:** `np.polyfit` relies heavily on complex SVD machinery to find coefficients, adding overhead.
**Action:** When a loop involves thousands of tiny, fixed-size mathematical operations (like 1D least-squares regression), use explicitly calculated values (e.g. solving equations using `np.sum`) rather than generalized, multi-dimensional array libraries like `np.polyfit`.
