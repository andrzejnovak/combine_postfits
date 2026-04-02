💡 What: Replaced np.polyfit with manual vectorized linear regression in the `linearity` function.
🎯 Why: np.polyfit incurs significant overhead (e.g. SVD computation, shape checking) which is unnecessary for calculating linearity on small histogram arrays.
📊 Impact: Expected ~3x performance improvement for the `linearity` calculations during sample sorting.
🔬 Measurement: A benchmarking script `test_polyfit.py` confirmed manual vectorized linear regression using np.sum was ~3x faster. Unit tests were also successfully executed to verify correctness.
