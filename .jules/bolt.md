## 2024-05-18 - Performance Tuning for `make_style_dict_yaml`
**Learning:** Found potential optimizations in how histograms are loaded in `make_style_dict_yaml`. `to_hist()` calls are computationally expensive.
**Action:** Let's measure the impact.

## 2024-05-18 - make_style_dict_yaml optimization
**Learning:** In `src/combine_postfits/utils.py`, `make_style_dict_yaml` calculates `yield` and `linearity` using nested list comprehensions that fetch histograms by string path (e.g., `fitDiag[f"shapes_{fit}/{ch}/{k}"]`) and call `to_hist()`. For each sample key, it searches across all fits and channels, calling `to_hist()` multiple times. By iterating through the Uproot directories once and extracting the histograms, and processing yield and linearity in a single pass over the histograms, we can avoid redundant `fitDiag[path]` lookups and `to_hist()` conversions.
**Action:** Refactor `make_style_dict_yaml` to loop over directories once, cache/process histograms locally, and significantly reduce `to_hist` calls.
