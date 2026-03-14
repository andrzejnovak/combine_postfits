## 2024-05-23 - Optimize 1D linear regression overhead in linearity calculation
**Learning:** `np.polyfit` uses generalized SVD routines which add massive overhead for simple 1D arrays like histogram bins. Manual calculation of the slope and intercept using `np.sum()` is ~3x faster.
**Action:** When performing simple 1D linear regressions on small arrays (like histogram bins) in performance-critical loops, prefer manual vectorized calculation using `np.sum` over `np.polyfit`.

## 2024-05-23 - Optimize 1D linear regression overhead in linearity calculation
**Learning:** `np.polyfit` uses generalized SVD routines which add massive overhead for simple 1D arrays like histogram bins. Manual calculation of the slope and intercept using `np.sum()` is ~3x faster.
**Action:** When performing simple 1D linear regressions on small arrays (like histogram bins) in performance-critical loops, prefer manual vectorized calculation using `np.sum` over `np.polyfit`.
