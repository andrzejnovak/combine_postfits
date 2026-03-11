## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-03-11 - Fast vectorized linear regression over np.polyfit
**Learning:** Using `np.polyfit(x, y, 1)` for 1D linear regression on small arrays (like histogram bins) carries a massive overhead (about 3x slower) compared to raw O(n) vectorized array math using `np.sum()`.
**Action:** When calculating simple metrics like slope or intercept for small inputs in a tight loop, compute them directly using vectorized mathematical definitions instead of relying on generalized polynomial fit routines.
