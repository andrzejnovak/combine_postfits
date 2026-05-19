## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-05-18 - Replacing Nested GetBinContent Loops with NumPy Buffers
**Learning:** In PyROOT, calling `GetBinContent` inside a Python double loop for large TH2 histograms incurs extremely high overhead (~2.3x slower or more) due to O(N^2) Python-to-C++ boundary crossings. We cannot use `np.asarray(h2)` directly as PyROOT often throws an IndexError.
**Action:** Always prefer bulk data extraction. Determine the correct dtype dynamically from `h2.ClassName()`, use `np.ndarray` with the buffer from `h2.GetArray()`, and appropriately slice to drop under/overflow bins (e.g., `arr[1:-1, 1:-1]`). This drastically speeds up plotting tools like `plot_cov`.
