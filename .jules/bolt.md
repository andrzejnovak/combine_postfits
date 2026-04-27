## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-04-27 - [ROOT Histogram Vectorization Optimization]
**Learning:** In PyROOT, calling `GetBinContent` inside nested Python loops incurs high overhead due to repeated Python-to-C++ boundary crossings. For large 2D histograms (e.g. covariance matrices), this becomes a major performance bottleneck (O(N^2)). Using `np.ndarray` with the ROOT array buffer directly bypasses these crossings and yields a significant speedup.
**Action:** Always prefer bulk vectorized data extraction using `np.ndarray(..., buffer=h.GetArray())` over nested `GetBinContent` loops when working with ROOT histograms in Python.
