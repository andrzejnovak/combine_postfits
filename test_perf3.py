import time

import uproot

from src.combine_postfits.utils import make_style_dict_yaml

f = uproot.open("tests/fitDiags/fit_diag_Abig.root")
start = time.time()
make_style_dict_yaml(f)
end = time.time()
print(f"Time: {end - start:.4f}s")
