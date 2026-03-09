import time

import uproot

from src.combine_postfits.utils import make_style_dict_yaml as original_fcn

f = uproot.open("tests/fitDiags/fit_diag_Abig.root")

start = time.time()
yield_dict = original_fcn(f)
end = time.time()
print(f"Original full: {end - start:.4f}s")
