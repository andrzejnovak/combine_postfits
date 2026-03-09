import pstats

p = pstats.Stats("stats2.prof")
p.sort_stats("time").print_callees("make_style_dict_yaml")
