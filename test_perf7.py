import cProfile
import io
import pstats

import uproot

from src.combine_postfits.utils import make_style_dict_yaml

f = uproot.open("tests/fitDiags/fit_diag_Abig.root")
pr = cProfile.Profile()
pr.enable()
make_style_dict_yaml(f)
pr.disable()
s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('time')
ps.print_stats('utils.py')
print(s.getvalue())
