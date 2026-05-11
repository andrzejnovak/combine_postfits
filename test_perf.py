import time
import uproot
import numpy as np
from combine_postfits.utils import make_style_dict_yaml

f = uproot.open("tests/fitDiags/fitDiagnosticsA.root")
start = time.time()
make_style_dict_yaml(f)
end = time.time()
print(f"Original time: {end - start:.2f}s")
