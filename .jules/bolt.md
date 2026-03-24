## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-03-01 - [High Overhead of `np.polyfit` on Small Arrays]
**Learning:** `np.polyfit` has significant overhead because it relies on full Singular Value Decomposition (SVD) routines under the hood. For simple 1D linear regression on small arrays (like histogram bins in `linearity()`), the overhead dominates the runtime.
**Action:** Replace `np.polyfit` with manual vectorized slope (`m`) and intercept (`b`) calculations using `np.sum`. This can yield a ~3x speedup on arrays under 1000 items while preserving correctness and reducing execution time in hot loops.
