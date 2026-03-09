import line_profiler
import uproot

from src.combine_postfits.utils import make_style_dict_yaml

f = uproot.open("tests/fitDiags/fit_diag_Abig.root")

lp = line_profiler.LineProfiler()
lp.add_function(make_style_dict_yaml)
lp.run("make_style_dict_yaml(f)")
lp.print_stats()
