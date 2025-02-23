import logging
import uproot
import matplotlib.pyplot as plt
import numpy as np
import hist
from cycler import cycler
from pkgutil import iter_modules


cmap6 = ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"]
cmap10 = [
    "#3f90da",
    "#ffa90e",
    "#bd1f01",
    "#94a4a2",
    "#832db6",
    "#a96b59",
    "#e76300",
    "#b9ac70",
    "#717581",
    "#92dadd",
]


def adjust_lightness(color, amount=0.5):
    import matplotlib.colors as mc
    import colorsys

    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    rgb = colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2])
    scaled_rgb = tuple([int(x * 255) for x in rgb])
    return "#{0:02x}{1:02x}{2:02x}".format(*scaled_rgb)


def module_exists(module_name):
    return module_name in (name for loader, name, ispkg in iter_modules())


def clean_yaml(style):
    for key in style:
        # Clean keys
        for elem in style[key]:
            if elem not in ["label", "color", "hatch", "contains"]:
                logging.warning(
                    f"Unexpected key: '{elem}' for sample: '{key}'. Allowed keys are: 'label', 'color', 'hatch', 'contains'."
                )
        # Standardize keys:
        for elem in ["label", "color", "hatch"]:
            if elem not in style[key]:
                style[key][elem] = None
        # Clean raw-strings (for latex in mpl)
        if style[key]["label"].startswith("r"):
            style[key]["label"] = style[key]["label"].split('"')[1]
        # Clean Nones:
        for elem in style[key]:
            if isinstance(style[key][elem], str) and style[key][elem].lower() == "none":
                style[key][elem] = None
        # Parse `contains` to a list
        if (
            "contains" in style[key]
            and style[key]["contains"] is not None
            and not isinstance(style[key]["contains"], list)
        ):
            style[key]["contains"] = style[key]["contains"].split()
    return style


def extract_mergemap(style):
    compound_keys = [
        key
        for key in style
        if "contains" in style[key] and style[key]["contains"] is not None
    ]
    return {key: style[key]["contains"] for key in compound_keys}


def fill_colors(style, cmap=None, no_duplicates=True):
    if cmap is None:
        cmap = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    taken = [
        style[key]["color"]
        for key in style
        if "color" in style[key] and style[key]["color"] is not None
    ]
    cmap_clean = cmap.copy()
    if no_duplicates:
        for c in taken:
            if c in cmap_clean:
                cmap_clean.remove(c)
    if len(cmap_clean) == 0:
        logging.error(
            "len(cmap) after cleaning is 0. Either pass longer 'cmap' or set `no_duplicates=False`."
        )
        cmap_clean = cmap
    cycler_iter = cycler("color", cmap_clean)()
    counter = 0
    taken = []
    for key in style:
        if "color" not in style[key] or style[key]["color"] is None:
            pop_col = next(cycler_iter)
            counter += 1
            logging.info(
                f'Key "color" not found for sample "{key}". Setting to: {pop_col}',
            )
            style[key]["color"] = (
                pop_col["color"]
                if pop_col["color"] not in taken
                else adjust_lightness(pop_col["color"], 1.4)
            )
            taken.append(pop_col["color"])
    if counter > len(cmap):
        logging.warning(
            f"'cmap' is too short. There will be {counter-len(cmap)} duplicate colors shown in lighter shades.",
        )
    for key, color, label in zip(
        ["data", "total_signal"], ["k", "red"], ["Data", "Signal"]
    ):
        if key not in style:
            logging.warning(
                f"Sample: '{key}' is not present in style_dict. It will be created with default values."
            )
            style[key] = {"color": color, "label": label}
    return style


def make_style_dict_yaml(fitDiag, cmap="tab10", sort=True, sort_peaky=False):
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
    avail_channels = [
        ch[:-2] for ch in fitDiag[f"shapes_{avail_fit_types[-1]}"] if ch.count("/") == 0
    ]

    def get_samples_fitDiag(fitDiag):
        snames = []
        for fit in avail_fit_types:
            try:
                for ch in [
                    ch[:-2] for ch in fitDiag[f"shapes_{fit}"] if ch.count("/") == 0
                ]:
                    snames += [k[:-2] for k in fitDiag[f"shapes_{fit}/{ch}"].keys()]
            except KeyError:
                print(f"Shapes: `shapes_{fit}` are missing from the fitDiagnostics")
        return sorted([k for k in list(set(snames)) if "covar" not in k])

    sample_keys = get_samples_fitDiag(fitDiag)

    # Sorting - yield/peakiness
    def linearity(h):
        _h = h.values()
        x = np.arange(len(_h))
        try:
            coef = np.polyfit(x, _h, 1)
        except:  # noqa
            return 0
        poly1d_fn = np.poly1d(coef)
        fy = poly1d_fn(x)
        residuals = abs(fy - _h) / np.sqrt(_h)
        return np.sum(np.nan_to_num(residuals, posinf=0, neginf=0))

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
        )
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
            logging.info(f"Sorting samples by yield")
        else:
            logging.info(
                f"EXPERIMENTAL: Sorting samples by a hybrid score: log(yield) * peakiness"
            )
        keys_sorted = [
            k
            for k, v in sorted(
                sort_score_dicts.items(), key=lambda item: item[1], reverse=True
            )
        ]
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
            "yield": float(f"{yield_dict[key]:.4f}"),
            # "sort_score": sort_score_dicts[key],
        }

    # Fill colors
    if cmap is None:
        colors = cmap
    # mpl maps
    elif cmap in plt.matplotlib.colormaps:
        colors = plt.matplotlib.colormaps[cmap].resampled(len(keys_sorted))(
            range(len(keys_sorted))
        )
    # metbrewer maps
    elif isinstance(cmap, str) and module_exists("met_brewer"):
        import met_brewer

        if cmap in met_brewer.MET_PALETTES:
            colors = met_brewer.met_brew(
                name=cmap, n=len(keys_sorted), brew_type="discrete"
            )
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
            logging.warning(
                f"cmap `{cmap}` not found. Available colormaps are {avail}."
            )
            if not has_met_brewer:
                logging.warning(
                    "Additional cmap are available from the `met_brewer` package when installed: "
                    "https://github.com/BlakeRMills/MetBrewer"
                )
    colors = [tuple(c) if isinstance(c, np.ndarray) else c for c in colors]
    # style = sort_by_yield(style, reverse=True)
    style = fill_colors(style, cmap=colors, no_duplicates=True)
    return style


def sort_by_yield(style, reverse=True):
    if "yield" not in style["data"]:
        return style
    sorted_keys = sorted(style, key=lambda k: style[k]["yield"], reverse=reverse)
    out = {"data": style["data"]}
    for k in sorted_keys:
        if k != "data" and "total" not in k:
            out[k] = style[k]
        if "total" in k:
            out[k] = style[k]
    for k in out.keys():
        del out[k]["yield"]
        del out[k]["sort_score"]
    return out


def prep_yaml(style):
    style = clean_yaml(style)
    style = fill_colors(style, cmap=cmap10)
    return style


# Formatting
def format_legend(ax, ncols=2, handles_labels=None, **kwargs):
    if handles_labels is None:
        handles, labels = ax.get_legend_handles_labels()
    else:
        handles, labels = handles_labels
    nentries = len(handles)

    kw = dict(framealpha=1, **kwargs)
    split = nentries // ncols * ncols
    leg1 = ax.legend(
        handles=handles[:split],
        labels=labels[:split],
        ncol=ncols,
        loc="upper right",
        **kw,
    )
    if nentries % 2 == 0:
        return leg1

    ax.add_artist(leg1)
    leg2 = ax.legend(
        handles=handles[split:],
        labels=labels[split:],
        ncol=nentries - nentries // ncols * ncols,
        **kw,
    )

    leg2.remove()

    leg1._legend_box._children.append(leg2._legend_handle_box)
    leg1._legend_box.stale = True
    return leg1


def format_categories(cats, n=2):
    # cat, cat \n cat, cat
    lab_cats = np.array(["x"] * (2 * len(cats) - 1), dtype="object")
    lab_cats[0::2] = cats
    lab_cats[1::2][n - 1 :: n] = "\n"
    for i in range(len(lab_cats)):
        if lab_cats[i] == "x":
            lab_cats[i] = ","
    return "".join(list(lab_cats))


# fitDiag extraction
def get_fit_val(fitDiag, val, fittype="fit_s", substitute=1.0):
    if fitDiag is None:
        return substitute
    if val in fitDiag.Get(fittype).floatParsFinal().contentsString().split(","):
        return fitDiag.Get(fittype).floatParsFinal().find(val).getVal()
    else:
        logging.warning(f"Parameter {val} not found in fitDiag. Returning {substitute}")
        return substitute


def get_fit_unc(fitDiag, val, fittype="fit_s", substitute=(0, 0)):
    if fitDiag is None:
        return substitute
    if val in fitDiag.Get(fittype).floatParsFinal().contentsString().split(","):
        rval = fitDiag.Get(fittype).floatParsFinal().find(val)
        if rval.hasAsymError():
            return (abs(rval.getAsymErrorLo()), rval.getAsymErrorHi())
        else:
            return (rval.getErrorLo(), rval.getErrorHi())
    else:
        logging.warning(f"Parameter {val} not found in fitDiag. Returning {substitute}")
        return substitute


# Object conversion
def tgasym_to_err(tgasym, restoreNorm=True):
    x, y = tgasym.values("x"), tgasym.values("y")
    xlo, xhi = tgasym.errors("low", axis="x"), tgasym.errors("high", axis="x")
    ylo, yhi = tgasym.errors("low", axis="y"), tgasym.errors("high", axis="y")
    bins = np.r_[(x - xlo), (x + xhi)[-1]]
    binwidth = xlo + xhi
    if restoreNorm:
        y = y * binwidth
        ylo = ylo * binwidth
        yhi = yhi * binwidth
    return y, bins, ylo, yhi


def tgasym_to_hist(tgasym, restoreNorm=True):
    y, bins, ylo, yhi = tgasym_to_err(tgasym, restoreNorm)
    h = hist.new.Var(bins, flow=False).Weight()
    h.view().value = y
    h.view().variance = y
    return h


def geth(name, shapes_dir, restoreNorm=True):
    if isinstance(shapes_dir[name], uproot.models.TGraph.Model_TGraphAsymmErrors_v3):
        return tgasym_to_hist(shapes_dir[name], restoreNorm=restoreNorm)
    else:
        h = shapes_dir[name].to_hist()
        if restoreNorm:
            h = h * h.axes[0].widths
        return h


def getha(name, channels, restoreNorm=True):
    for shapes_dir in channels:
        if name not in shapes_dir:
            logging.debug(
                f"    Sample: '{name}' not found in channel '{shapes_dir}' and will be skipped."
            )
    return sum(
        [
            geth(name, shapes_dir, restoreNorm=restoreNorm)
            for shapes_dir in channels
            if name in shapes_dir
        ]
    )


def geths(names, channels, restoreNorm=True, style_dict=None):
    if style_dict is not None:
        sorted_names = [k for k, v in style_dict.items() if k in names]
        assert len(sorted_names) == len(
            names
        ), f"Sorting incomplete: {names} -> {sorted_names}"
        names = sorted_names
    if isinstance(channels, list):  # channels = [shapes_dir, shapes_dir]
        return {name: getha(name, channels, restoreNorm=restoreNorm) for name in names}
    else:  # channels = shapes_dir
        return {name: geth(name, channels, restoreNorm=restoreNorm) for name in names}


def merge_hists(hist_dict, merge_map):
    for k, v in merge_map.items():
        if k in hist_dict and k != v[0]:
            logging.warning(
                f"  Mapping `'{k}' : {v}` will replace existing histogram: '{k}'."
            )
        to_merge = []
        for name in v:
            if name not in hist_dict:
                logging.warning(
                    f"  Histogram '{name}' is not available in channel for a merge {v} -> '{k}' and won't be part of the merge."
                )
            else:
                to_merge.append(hist_dict[name])
        if len(to_merge) > 0:
            hist_dict[k] = sum(to_merge)
        else:
            logging.warning(f"  No histograms available for merge {v} -> '{k}'.")
    return hist_dict
