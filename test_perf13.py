import time

import uproot

f = uproot.open("tests/fitDiags/fit_diag_Abig.root")

def make_style_dict_yaml_patched(fitDiag, cmap="tab10", sort=True, sort_peaky=False):
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

    t1 = time.time()

    yield_dict = {
        k: sum(
            [
                sum(fitDiag[f"shapes_{fit}/{ch}/{k}"].to_hist().values())
                for fit in avail_fit_types
                for ch in avail_channels
                if f"shapes_{fit}/{ch}/{k}" in fitDiag
                and hasattr(fitDiag[f"shapes_{fit}/{ch}/{k}"], "to_hist")
                and "total" not in k  # Sum only TH1s, data is black anyway
            ]
        )
        for k in sample_keys
    }
    t2 = time.time()
    print(f"yield dict took {t2 - t1:.4f}s")

    linearity_dict = {
        k: np.mean(
            [
                linearity(fitDiag[f"shapes_{fit}/{ch}/{k}"].to_hist())
                for fit in avail_fit_types
                for ch in avail_channels
                if f"shapes_{fit}/{ch}/{k}" in fitDiag
                and hasattr(fitDiag[f"shapes_{fit}/{ch}/{k}"], "to_hist")
                and "total" not in k  # Sum only TH1s, data is black anyway
            ]
            + [0]  # pad 0 to prevent mean on empty list
        )
        for k in sample_keys
    }
    t3 = time.time()
    print(f"linearity dict took {t3 - t2:.4f}s")

import numpy as np

make_style_dict_yaml_patched(f)
