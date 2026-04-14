## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Removed redundant directory pathing and `to_hist` calls in Uproot metrics calculation
**Learning:** In `make_style_dict_yaml`, calculating sum yields and linearities was being done via key-based string path lookup. Every key (`k`) was triggering another full parsing of the Uproot file (`fitDiag[f"shapes_{fit}/{ch}/{k}"]`), and worse, calling `to_hist()` separately for each metric, leading to O(N^2) allocations and array unpacking.
**Action:** When computing metrics across all histograms in a ROOT file, use a directory-driven approach. Traverse down `fitDiag['shapes_fit']['ch']`, use `.keys(cycle=False)`, load the object, call `.to_hist()` exactly ONCE, and calculate all metrics synchronously.
