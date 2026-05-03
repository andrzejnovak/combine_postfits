## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Replace O(N^2) list flattening with any() for boolean checks
**Learning:** Checking for key existence across multiple dictionaries using `key not in list(set(sum([c.keys() for c in channels], [])))` creates a massive performance penalty. It constructs nested lists, flattens them, converts them to sets, and then back to lists just for a membership check.
**Action:** When checking if a key exists in an array of dictionaries (like Uproot directory objects), use short-circuiting generators like `any(key in c for c in channels)` instead. This stops iteration immediately upon finding the key, saving significant time and memory reallocation overhead.
