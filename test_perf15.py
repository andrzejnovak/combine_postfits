import time

import numpy as np
import uproot

f = uproot.open("tests/fitDiags/fit_diag_Abig.root")

def make_style_dict_yaml_optimized(fitDiag, cmap="tab10", sort=True, sort_peaky=False):
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
    print("got keys")

    # Sorting - yield/peakiness
    def linearity(h):
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

    t1 = time.time()

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

    t2 = time.time()
    print(f"combined loops took {t2 - t1:.4f}s")

make_style_dict_yaml_optimized(f)
