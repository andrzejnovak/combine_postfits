import argparse
import logging
import pprint
from typing import Any

import hist
import matplotlib.legend
import matplotlib.pyplot as plt
import numpy as np
import uproot
from cycler import cycler

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

# set up pretty printer for logging
pp = pprint.PrettyPrinter(indent=2, sort_dicts=False)


def log_pretty(obj) -> str:
    pretty_out = f"{pp.pformat(obj)}"
    return f"{pretty_out}\n"


def str2bool(v: str | bool) -> bool:
    """Convert string (e.g. 'yes', 'true', '1') to boolean."""
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def adjust_lightness(color: str, amount: float = 0.5) -> str:
    """Adjust lightness of a color ( >1 is lighter, <1 is darker)."""
    import colorsys

    import matplotlib.colors as mc

    try:
        c = mc.cnames[color]
    except Exception:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    rgb = colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2])
    scaled_rgb = tuple([int(x * 255) for x in rgb])
    return "#{0:02x}{1:02x}{2:02x}".format(*scaled_rgb)


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Configure logging with RichHandler. Shared by CLI entry points."""
    import click
    from rich.logging import RichHandler

    log_level = logging.WARNING
    if verbose:
        log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG
    for noisy in ["matplotlib", "fsspec", "ROOT", "boost_histogram"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click])],
    )


def clean_yaml(style: dict) -> dict:
    """Clean and standardize the style dictionary (parse None, fix keys)."""
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
        # Clean raw-strings (for latex in mpl), e.g. r"$H_{bb}$" -> $H_{bb}$
        lbl = style[key]["label"]
        if isinstance(lbl, str) and lbl.startswith(('r"', "r'")):
            quote = lbl[1]
            style[key]["label"] = lbl[2:].rsplit(quote, 1)[0]
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


def extract_mergemap(style: dict) -> dict:
    """Extract sample merging rules from the style dictionary."""
    compound_keys = [key for key in style if "contains" in style[key] and style[key]["contains"] is not None]
    return {key: style[key]["contains"] for key in compound_keys}


def fill_colors(style: dict, cmap: list | str | None = None, no_duplicates: bool = True) -> dict:
    """Assign colors to samples in the style dict using a colormap."""
    if cmap is None:
        cmap = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    taken = [style[key]["color"] for key in style if "color" in style[key] and style[key]["color"] is not None]
    cmap_clean = cmap.copy()
    if no_duplicates:
        for c in taken:
            if c in cmap_clean:
                cmap_clean.remove(c)
    if len(cmap_clean) == 0:
        logging.error("len(cmap) after cleaning is 0. Either pass longer 'cmap' or set `no_duplicates=False`.")
        cmap_clean = cmap
    cycler_iter = cycler("color", cmap_clean)()
    counter = 0
    taken = []
    for key in style:
        if "color" not in style[key] or style[key]["color"] is None:
            pop_col = next(cycler_iter)["color"]
            counter += 1
            logging.info(
                f'Key "color" not found for sample "{key}". Setting to: {pop_col}',
            )
            # Keep lightening until the color is unique so repeats beyond 2x don't collapse.
            # Bound the attempts: adjust_lightness saturates at white, so an unbounded loop could
            # spin forever once two colors both reach white; accept a duplicate after that.
            assigned = pop_col
            for _ in range(10):
                if assigned not in taken:
                    break
                assigned = adjust_lightness(assigned, 1.4)
            style[key]["color"] = assigned
            taken.append(assigned)
    if counter > len(cmap):
        logging.warning(
            f"'cmap' is too short. There will be {counter - len(cmap)} duplicate colors shown in lighter shades.",
        )
    for key, color, label in zip(["data", "total_signal"], ["k", "red"], ["Data", "Signal"]):
        if key not in style:
            logging.warning(f"Sample: '{key}' is not present in style_dict. It will be created with default values.")
            style[key] = {"color": color, "label": label}
    return style


def prep_yaml(style: dict) -> dict:
    """Normalize a raw style dict: clean fields and fill in default colors."""
    style = clean_yaml(style)
    style = fill_colors(style, cmap=cmap10)
    return style


def make_style_dict_yaml(
    fitDiag: uproot.ReadOnlyDirectory, cmap: str = "tab10", sort: bool = True, sort_peaky: bool = False
) -> dict:
    """Generate a style dictionary from a fitDiagnostics file."""
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
        _h = h.values()
        n = len(_h)
        if n <= 1:
            return 0

        x = np.arange(n, dtype=float)
        sum_x = x.sum()
        sum_y = _h.sum()
        sum_xx = (x * x).sum()
        sum_xy = (x * _h).sum()

        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            return 0

        m = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - m * sum_x) / n

        fy = m * x + b
        residuals = abs(fy - _h) / np.sqrt(_h)
        return np.nan_to_num(residuals, posinf=0, neginf=0).sum()

    # Convert each histogram once (uproot's to_hist is not memoized) and index each ROOT key
    # a single time; reuse the cached hist objects for both the yield sum and the linearity score.
    hist_cache = {k: [] for k in sample_keys}
    for k in sample_keys:
        if "total" in k:  # Sum only TH1s, data is black anyway
            continue
        for fit in avail_fit_types:
            for ch in avail_channels:
                key = f"shapes_{fit}/{ch}/{k}"
                if key in fitDiag and hasattr(fitDiag[key], "to_hist"):
                    hist_cache[k].append(fitDiag[key].to_hist())

    yield_dict = {k: sum(sum(h.values()) for h in hist_cache[k]) for k in sample_keys}
    linearity_dict = {
        # pad 0 to prevent mean on empty list
        k: np.mean([linearity(h) for h in hist_cache[k]] + [0])
        for k in sample_keys
    }
    sort_score_dicts = {}
    for k, v in yield_dict.items():
        if sort_peaky:
            # Clamp the yield so a zero/negative sum doesn't produce log(0)=-inf (and -inf*0=nan),
            # which would make the sort ordering undefined.
            sort_score_dicts[k] = np.log(max(v, 1e-9)) * (linearity_dict[k])
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
    else:
        try:
            import met_brewer

            if cmap in met_brewer.MET_PALETTES:
                colors = met_brewer.met_brew(name=cmap, n=len(keys_sorted), brew_type="discrete")
            else:
                colors = None
        except ImportError:
            colors = None
    if colors is None:
        colors = cmap10
        if cmap is None:
            logging.warning("No cmap passed, defaulting to CMS-style 10 colors cmap")
        else:
            avail = list(plt.matplotlib.colormaps)
            try:
                import met_brewer

                avail += met_brewer.MET_PALETTES
            except ImportError:
                logging.warning(
                    "Additional cmap are available from the `met_brewer` package when installed: "
                    "https://github.com/BlakeRMills/MetBrewer"
                )
            logging.warning(f"cmap `{cmap}` not found. Available colormaps are {avail}.")
    colors = [tuple(c) if isinstance(c, np.ndarray) else c for c in colors]
    style = fill_colors(style, cmap=colors, no_duplicates=True)
    return style


# Formatting
def format_legend(
    ax: plt.Axes, ncols: int = 2, handles_labels: tuple | None = None, **kwargs
) -> matplotlib.legend.Legend:
    """Format the legend to hold huge number of entries.

    Splits the legend into two columns to avoid extending off the plot.
    """
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
    if nentries % ncols == 0:
        return leg1

    ax.add_artist(leg1)
    leg2 = ax.legend(
        handles=handles[split:],
        labels=labels[split:],
        ncol=nentries - split,
        **kw,
    )

    leg2.remove()

    # Merge the overflow column into leg1 via matplotlib's (private) legend box. Guard it so a
    # future matplotlib that restructures these internals degrades to a single legend rather than crashing.
    try:
        leg1._legend_box._children.append(leg2._legend_handle_box)
        leg1._legend_box.stale = True
    except AttributeError:
        logging.warning("Could not merge overflow legend column via matplotlib internals; using a single legend.")
        leg1.remove()
        leg1 = ax.legend(handles=handles, labels=labels, ncol=ncols, loc="upper right", **kw)
    return leg1


def format_categories(cats: list[str], n: int = 2) -> str:
    """Format category names with line breaks every `n` entries."""
    lines = []
    for i in range(0, len(cats), n):
        lines.append(",".join(cats[i : i + n]))
    return "\n".join(lines)


# fitDiag extraction
def get_fit_val(fitDiag: "Any", val: str, fittype: str = "fit_s", substitute: float = 1.0) -> float:
    """Extract a float parameter value from the fitDiagnostics file."""
    if fitDiag is None:
        return substitute
    if val in fitDiag.Get(fittype).floatParsFinal().contentsString().split(","):
        return fitDiag.Get(fittype).floatParsFinal().find(val).getVal()
    else:
        logging.warning(f"Parameter {val} not found in fitDiag. Returning {substitute}")
        return substitute


def get_fit_unc(
    fitDiag: "Any", val: str, fittype: str = "fit_s", substitute: tuple[float, float] = (0.0, 0.0)
) -> tuple[float, float]:
    """Extract a parameter uncertainty (lo, hi) from the fitDiagnostics file."""
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
def tgasym_to_err(
    tgasym: uproot.model.Model, restoreNorm: bool = True
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert TGraphAsymmErrors to numpy arrays (y, bins, ylo, yhi)."""
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


def tgasym_to_hist(tgasym: uproot.model.Model, restoreNorm: bool = True) -> hist.Hist:
    """Convert TGraphAsymmErrors to a boost-histogram/hist object."""
    y, bins, ylo, yhi = tgasym_to_err(tgasym, restoreNorm)
    h = hist.new.Var(bins, flow=False).Weight()
    h.view().value = y
    h.view().variance = y
    return h


def geth(name: str, shapes_dir: uproot.ReadOnlyDirectory, restoreNorm: bool = True) -> hist.Hist:
    """Retrieve a histogram or TGraph from a ROOT directory as a hist object."""
    if isinstance(shapes_dir[name], uproot.models.TGraph.Model_TGraphAsymmErrors_v3):
        return tgasym_to_hist(shapes_dir[name], restoreNorm=restoreNorm)
    else:
        h = shapes_dir[name].to_hist()
        if restoreNorm:
            h = h * h.axes[0].widths
        return h


def getha(name: str, channels: list[uproot.ReadOnlyDirectory], restoreNorm: bool = True) -> hist.Hist:
    """Retrieve and sum histograms for a sample across multiple channels."""
    hists = []
    for shapes_dir in channels:
        if name in shapes_dir:
            hists.append(geth(name, shapes_dir, restoreNorm=restoreNorm))
        else:
            logging.debug(f"    Sample: '{name}' not found in channel '{shapes_dir}' and will be skipped.")
    if hists:
        return sum(hists)
    # Sample absent from every channel: return a zero-filled hist matching the channel binning
    # instead of the int 0 that sum([]) would yield (which breaks downstream .values()/arithmetic).
    for shapes_dir in channels:
        for tmpl in shapes_dir.keys(cycle=False):
            try:
                return geth(tmpl.split(";")[0], shapes_dir, restoreNorm=restoreNorm) * 0
            except Exception:
                continue
    raise ValueError(f"Sample '{name}' not found in any channel and no template histogram is available.")


def geths(
    names: list[str],
    channels: uproot.ReadOnlyDirectory | list[uproot.ReadOnlyDirectory],
    restoreNorm: bool = True,
    style_dict: dict | None = None,
) -> dict[str, hist.Hist]:
    """Retrieve multiple histograms, optionally sorting them by style_dict order."""
    if style_dict is not None:
        sorted_names = [k for k, v in style_dict.items() if k in names]
        assert len(sorted_names) == len(names), f"Sorting incomplete: {names} -> {sorted_names}"
        names = sorted_names
    if isinstance(channels, list):  # channels = [shapes_dir, shapes_dir]
        return {name: getha(name, channels, restoreNorm=restoreNorm) for name in names}
    else:  # channels = shapes_dir
        return {name: geth(name, channels, restoreNorm=restoreNorm) for name in names}


def merge_hists(hist_dict: dict[str, hist.Hist], merge_map: dict[str, list[str]]) -> dict[str, hist.Hist]:
    """Merge histograms according to the map {new_key: [old_keys...]}."""
    for k, v in merge_map.items():
        if k in hist_dict and k != v[0]:
            logging.warning(f"  Mapping `'{k}' : {v}` will replace existing histogram: '{k}'.")
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


def _string_to_slice(s: str) -> slice:
    """Convert string "start:stop:step" to slice object (supports complex for value-based)."""
    parts = s.split(":")
    parts = [complex(p) if p else None for p in parts]
    return slice(*parts)


def _ensure_slice_by_ix(s: slice, edges: np.ndarray) -> slice:
    """Convert value-based slice (using imaginary) to index-based slice.

    Convention: 5j means "the bin containing value 5" (lookup by edge).
    A plain int/float means a direct bin index.
    Omitted bounds (e.g. "3j:" or ":6j") default to the array ends.
    """
    if s.start is None:
        start = 0
    elif s.start.imag != 0:
        start = np.searchsorted(edges, s.start.imag, side="right") - 1
    else:
        start = int(s.start.real)
    if s.stop is None:
        stop = len(edges) - 1
    elif s.stop.imag != 0:
        stop = np.searchsorted(edges, s.stop.imag, side="right")
    else:
        stop = int(s.stop.real)
    step = None if s.step is None else int(s.step.real)
    return slice(int(start), int(stop), step)
