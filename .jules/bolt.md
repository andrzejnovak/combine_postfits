## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2026-04-22 - Optimize ROOT TH2 Data Extraction
**Learning:** Calling `GetBinContent` in nested Python loops on ROOT histograms is a major performance bottleneck due to crossing the Python-C++ boundary for every bin.
**Action:** Extract the raw buffer using `h.GetArray()`, cast it with `np.frombuffer`, reshape to include underflow/overflow bins, and then slice the view to extract the data array. This results in an order of magnitude speedup (~30x).
