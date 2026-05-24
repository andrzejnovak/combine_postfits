## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2024-05-24 - Precomputing parsed arguments to eliminate redundant inner-loop splitting
**Learning:** Found redundant string splitting using list/dictionary comprehensions based on `args.cats.split()` inside inner loops. Repeated O(N) operations within tight loop processing significantly impacts category processing scalability.
**Action:** Precompute these parsed string collections immediately after argument validation in `make_plots.py` and reuse the precomputed variables (`merged_cats`, `cat_map`, `cats_parsed`) across downstream loops.
