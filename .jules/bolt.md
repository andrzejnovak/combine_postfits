## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-03-09 - Avoided repeated list concatenations and deepcopies in tight loops
**Learning:** In `plot_postfits.py`'s `remove_tiny` filter, `get_hist(key)` implicitly performed a `deepcopy` on the histogram object, and the list `bkgs + sigs + project` was being reconstructed on every iteration over `hist_keys`. This created significant O(N) memory allocation and recursive O(N^2) overhead for simple read checks.
**Action:** Always precompute invariant list concatenations to a `set` before loops. When only reading histogram values for aggregation operations, pass `raw=True` to `get_hist` (if available) to bypass the deepcopy, and chain it with the native `.sum()` to avoid Numpy dispatch overhead.
