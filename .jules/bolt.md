## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Removed O(N^2) path lookups in Uproot dictionary generation
**Learning:** `make_style_dict_yaml` computed properties like yield and linearity using list comprehensions that generated full `path/to/key` string lookups over multiple loops. When checking file existence `if f"shapes_{fit}/{ch}/{k}" in fitDiag`, Uproot re-parsed the directory path and repeatedly queried its keys. This turned a process with O(N) objects into O(N^2) lookups.
**Action:** When gathering metrics from many objects in an Uproot file, access the parent directory object once (`dir_obj = fitDiag[dir_path]`), call `dir_obj.classnames()` or `dir_obj.keys(cycle=False)`, and iterate locally over the items.
