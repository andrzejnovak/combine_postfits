## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.
## 2025-02-19 - Replacing N^2 path-lookup algorithms with direct directory indexing
**Learning:**  iteratively probed paths over multiple nested levels resulting in O(N^2) path parsing latency with Uproot. This combined with invoking  repeatedly caused huge delays for large root files.
**Action:** Transformed multi-pass lookups into a single directory pass () and substituted  with analytic unrolled evaluations using raw metrics for ~2-3x speedup.
## 2025-02-19 - Replacing N^2 path-lookup algorithms with direct directory indexing
**Learning:** `make_style_dict_yaml` iteratively probed paths over multiple nested levels resulting in O(N^2) path parsing latency with Uproot. This combined with invoking `np.polyfit` repeatedly caused huge delays for large root files.
**Action:** Transformed multi-pass lookups into a single directory pass (`dir_obj.keys(cycle=False)`) and substituted `np.polyfit` with analytic unrolled evaluations using raw metrics for ~2-3x speedup.
