## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2026-06-19 - Optimize Uproot directory traversal
**Learning:** Repeated full-path lookups and object extractions inside nested loops in Uproot cause severe overhead. The optimal pattern is directory-driven: iterate through available Uproot directories using .keys(cycle=False), extract objects once, and compute all metrics simultaneously.
**Action:** Replaced O(N^2) list comprehensions with single-pass directory loop in make_style_dict_yaml.
