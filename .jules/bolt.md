## 2025-02-19 - Removed redundant O(n) scan in inner loop
**Learning:** `np.max([np.max(h.values()) for h in hist_dict.values()])` was being called inside a nested helper function (`hist_dict_fcn`) that executed multiple times for each histogram plotted. Profiling showed this dominated execution time because it was calculating the global max recursively instead of caching it once.
**Action:** Always look for invariants in nested loops and inner functions. Moved the `_max_value_global` calculation outside the `hist_dict_fcn` to speed up plotting. Remember NOT to use `functools.lru_cache` for `hist_dict_fcn` since it returns deepcopies that are mutated by the caller.

## 2025-02-19 - Replace O(N^2) sum([]) flattening with comprehensions
**Learning:** Using `sum([list_of_lists], [])` to flatten nested lists in Python executes in O(N^2) time because it repeatedly creates and copies elements to new intermediate lists. This pattern was used in `plot_postfits.py` and `make_plots.py` and scaled poorly with many Uproot histogram keys or categories.
**Action:** Replace `sum([], [])` with list/set comprehensions (`[x for l in lists for x in l]`) or `itertools.chain.from_iterable()` for O(N) flattening. When checking for element existence across multiple lists/dicts, use short-circuiting (`any(item in sub for sub in parent)`) rather than flattening the entire structure.
