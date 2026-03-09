import time

import numpy as np
import uproot

from src.combine_postfits.utils import make_style_dict_yaml as original_fcn

f = uproot.open("tests/fitDiags/fit_diag_Abig.root")

def make_style_dict_yaml_optimized(fitDiag, cmap="tab10", sort=True, sort_peaky=False):
    import logging

    import matplotlib.pyplot as plt

    from src.combine_postfits.utils import cmap10, fill_colors, module_exists

    style_base = {
        "data": {"label": "Data", "color": "black", "hatch": None, "yield": 0},
        "total_signal": {
            "label": "Total Signal",
            "color": "red",
            "hatch": None,
            "yield": 0,
        },
    }

    fit_types = ["prefit", "fit_s", "fit_b"]
    avail_fit_types = [f for f in fit_types if f"shapes_{f}" in fitDiag]
    avail_channels = [ch[:-2] for ch in fitDiag[f"shapes_{avail_fit_types[-1]}"] if ch.count("/") == 0]

    def get_samples_fitDiag(fitDiag):
        snames = []
        for fit in avail_fit_types:
            try:
                for ch in [ch[:-2] for ch in fitDiag[f"shapes_{fit}"] if ch.count("/") == 0]:
                    snames += [k[:-2] for k in fitDiag[f"shapes_{fit}/{ch}"].keys()]
            except KeyError:
                print(f"Shapes: `shapes_{fit}` are missing from the fitDiagnostics")
        return sorted([k for k in list(set(snames)) if "covar" not in k])

    sample_keys = get_samples_fitDiag(fitDiag)

    # Sorting - yield/peakiness
    def linearity(h):
        import numpy as np
        _h = h.values()
        x = np.arange(len(_h))
        if len(_h) <= 1:
            return 0
        try:
            coef = np.polyfit(x, _h, 1)
        except:  # noqa
            return 0
        poly1d_fn = np.poly1d(coef)
        fy = poly1d_fn(x)
        residuals = abs(fy - _h) / np.sqrt(_h)
        return np.sum(np.nan_to_num(residuals, posinf=0, neginf=0))

    yield_dict = {k: 0 for k in sample_keys}
    linearity_lists = {k: [] for k in sample_keys}

    for fit in avail_fit_types:
        for ch in avail_channels:
            dir_path = f"shapes_{fit}/{ch}"
            if dir_path in fitDiag:
                dir_obj = fitDiag[dir_path]
                dir_keys = dir_obj.keys()
                # Use standard parsing to match what we do for keys
                available_objects = {}
                for key_cycle in dir_keys:
                    name, cycle = key_cycle.split(';')
                    cycle = int(cycle)
                    # keep the highest cycle just in case
                    if name not in available_objects or cycle > available_objects[name][1]:
                        available_objects[name] = (key_cycle, cycle)

                for k in sample_keys:
                    if "total" in k:
                        continue
                    if k in available_objects:
                        key_to_use = available_objects[k][0]
                        obj = dir_obj[key_to_use]
                        if hasattr(obj, "to_hist"):
                            h = obj.to_hist()
                            yield_dict[k] += sum(h.values())
                            linearity_lists[k].append(linearity(h))

    linearity_dict = {
        k: np.mean(linearity_lists[k] + [0])
        for k in sample_keys
    }

    sort_score_dicts = {}
    for k, v in yield_dict.items():
        if sort_peaky:
            sort_score_dicts[k] = np.log(v) * (linearity_dict[k])
        else:
            sort_score_dicts[k] = v
    if sort:
        if not sort_peaky:
            logging.info("Sorting samples by yield")
        else:
            logging.info("EXPERIMENTAL: Sorting samples by a hybrid score: log(yield) * peakiness")
        keys_sorted = [k for k, v in sorted(sort_score_dicts.items(), key=lambda item: item[1], reverse=True)]
    else:
        keys_sorted = sample_keys
    # Fill dummy style dict
    style = style_base.copy()
    for key in keys_sorted:
        if key == "data" or "total" in key:  # Skip totals
            continue
        if key not in style:
            style[key] = {
                "label": key,
                "color": None,
                "hatch": None,
                "yield": float(f"{yield_dict[key]:.4f}"),
                # "sort_score": float(f"{sort_score_dicts[key]:.4f}"),
            }
    # Add total, total_signal, total_background at the end
    for key in ["total", "total_background"]:
        style[key] = {
            "label": key,
            "color": None,
            "hatch": None,
            # "yield": float(f"{yield_dict[key]:.4f}"),
            # "sort_score": sort_score_dicts[key],
        }

    # Fill colors
    if cmap is None:
        colors = cmap
    # mpl maps
    elif cmap in plt.matplotlib.colormaps:
        colors = plt.matplotlib.colormaps[cmap].resampled(len(keys_sorted))(range(len(keys_sorted)))
    # metbrewer maps
    elif isinstance(cmap, str) and module_exists("met_brewer"):
        import met_brewer

        if cmap in met_brewer.MET_PALETTES:
            colors = met_brewer.met_brew(name=cmap, n=len(keys_sorted), brew_type="discrete")
        else:
            colors = None
    else:
        colors = None
    if colors is None:
        colors = cmap10
        if cmap is None:
            logging.warning("No cmap passed, defaulting to CMS-style 10 colors cmap")
        else:
            avail = list(plt.matplotlib.colormaps)
            has_met_brewer = module_exists("met_brewer")
            if has_met_brewer:
                avail += met_brewer.MET_PALETTES
            logging.warning(f"cmap `{cmap}` not found. Available colormaps are {avail}.")
            if not has_met_brewer:
                logging.warning(
                    "Additional cmap are available from the `met_brewer` package when installed: "
                    "https://github.com/BlakeRMills/MetBrewer"
                )
    colors = [tuple(c) if isinstance(c, np.ndarray) else c for c in colors]
    # style = sort_by_yield(style, reverse=True)
    style = fill_colors(style, cmap=colors, no_duplicates=True)
    return style

start = time.time()
yield_dict = make_style_dict_yaml_optimized(f)
end = time.time()
print(f"Optimized full: {end - start:.4f}s")

start = time.time()
yield_dict_orig = original_fcn(f)
end = time.time()
print(f"Original full: {end - start:.4f}s")

# Check if they produce the same result
if yield_dict == yield_dict_orig:
    print("Results are equal!")
else:
    print("Results differ!")
