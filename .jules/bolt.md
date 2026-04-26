## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-04-26 - Vectorize ROOT TH2 extraction using np.ndarray buffer
**Learning:** Extracting data from ROOT `TH2` histograms using nested loops over `GetBinContent` in Python is extremely slow due to the high overhead of repeatedly crossing the Python-C++ boundary. The same logic took ~0.31s with loops and ~0.009s with vectorization (~34x speedup).
**Action:** When extracting data from `TH2D` objects into Python, determine the equivalent NumPy dtype (using `ClassName()`), create an `np.ndarray` viewing the buffer directly (`h2.GetArray()`), and use slicing/transposing (e.g. `arr[1:-1, 1:-1].T`) to bypass the C++ interface and drop overflow/underflow bins.
