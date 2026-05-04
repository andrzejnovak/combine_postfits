## 2026-05-04 - Optimize Style Dictionary Generation
**Learning:** In `make_style_dict_yaml`, repeatedly looking up paths in Uproot like `fitDiag[f"shapes_{fit}/{ch}/{k}"]` causes severe O(N^2) latency due to redundant directory existence and string parsing checks inside Uproot, taking >11 seconds for large files.
**Action:** Shift from key-driven lookups to directory-driven traversals. By extracting the directory object `ch_dir = fitDiag[f"shapes_{fit}/{ch}"]` once, and then iterating over its items using `ch_dir.classnames()`, we reduce the complexity to O(N). Filtering out `"TDirectory"` and `"TGraph"` objects directly from the classnames mapping eliminates the overhead of instantiating Python objects solely to check if they have a `.to_hist()` method.

## 2026-05-04 - Fast 1D Linear Regression
**Learning:** Using `np.polyfit(x, y, 1)` for tiny arrays (computing linearity inside a loop) incurs massive overhead because NumPy delegates to a generalized SVD routine capable of solving complex multi-dimensional fits.
**Action:** Replace `np.polyfit` in performance-critical loops with an explicit, vectorized least-squares calculation using standard `np.sum()`. This manual O(N) calculation yields identical mathematical results but runs ~5.7x faster than the generalized `polyfit` solver.
