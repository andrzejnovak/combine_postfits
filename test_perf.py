import cProfile

import uproot

f = uproot.open("tests/fitDiags/fit_diag_Abig.root")

cProfile.run("make_style_dict_yaml(f)", "stats.prof")

import pstats

p = pstats.Stats("stats.prof")
p.sort_stats("time").print_stats(20)
