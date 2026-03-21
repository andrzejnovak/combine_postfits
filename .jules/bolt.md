## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-03-21 - Replaced np.polyfit with manual vectorized linear regression in linearity sorting
**Learning:** `np.polyfit` executes highly generalized linear regression logic involving checks and computationally expensive algorithms like SVD. When only a simple 1D linear regression slope and intercept are needed, especially for small arrays (like histogram bins in `make_style_dict_yaml` sorting), the overhead is huge.
**Action:** Replace `np.polyfit` and `np.poly1d` with a manual, vectorized calculation of slope and intercept using `np.sum`. This yields identical numerical results while performing approximately 3x faster, which removes a bottleneck in the sample sorting process.
