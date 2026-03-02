## 2024-03-02 - hist_dict_fcn caching
**Learning:** `functools.lru_cache` and extracting global computations out of `hist_dict_fcn` are known optimizations, but they only yield minor runtime improvements because the bottleneck often lies in matplotlib rendering.
**Action:** Do not rely on caching alone for performance wins in this module; profile before attempting optimization.
