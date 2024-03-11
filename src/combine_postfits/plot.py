import typing
import typing_extensions
from collections import defaultdict
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typeguard import typechecked
import logging
import pprint
import numpy as np
from scipy import stats
import mplhep as hep

from .utils import cmap10
from .utils import extract_mergemap, fill_colors
from .utils import format_legend, format_categories
from .utils import get_fit_val, get_fit_unc
from .utils import getha, geths, merge_hists

np.seterr(divide="ignore", invalid="ignore")

# set up pretty printer for logging
pp = pprint.PrettyPrinter(indent=2, sort_dicts=False)


def log_pretty(obj):
    pretty_out = f"{pp.pformat(obj)}"

    return f"{pretty_out}\n"


@typechecked
def plot(
    fitDiag_uproot,
    fit_type: str = "prefit",  # 'prefit' | 'fit_s' | 'fit_b'
    cats: str | list[str] | None = None,
    # Sample plotting opts
    sigs: list[str]
    | None = None,  # List of samples considered signals, by default matches to `total_signal`
    bkgs: list[str]
    | None = None,  # List of samples considered backaground - exclude QCD
    onto: str | None = None,  # large background to plot others onto typically QCD
    project: list[str]
    | None = None,  # Project (duplicate) some samples onto the x-axis for readability
    project_signal: list[float | int]
    | None = None,  # Plot projected total signal on x-axis, scale by `project_signal`
    remove_tiny: bool
    | float
    | int
    | str = False,  # Remove enteries with total yield below treshold eg. {False | 10 | '5%'}
    # Style opts
    restoreNorm=True,  # Combine outputs binwnormed results - restores to nominal
    fitDiag_root=None,  # ROOT fitDiagnostics file to read fit results and display signal strength
    rmap: dict | None = None,
    style: dict | None = None,  # Style YAML
    merge: dict[str, list]
    | None = None,  # {new_key: [old_key1, old_key2]} overwrites settings in style yaml
    clipx: bool = False,  # Clip edge bins when empty
    cat_info: bool
    | int = 2,  # Number of cats to display per line. Set ``False`` to disable cat info
    chi2: bool = False,  # Calculated and display chi2 of data to total shapes
) -> tuple:
    # Prep
    style = style.copy()
    fit_shapes_name = f"shapes_{fit_type}"
    if cats is None:
        cats = [fitDiag_uproot[f"{fit_shapes_name}"].keys()[0].split(";")[0]]
    elif isinstance(cats, str):
        cats = [cats]
    logging.info(f"Plotting `{fit_shapes_name}` for categories: {','.join(cats)}.")
    if restoreNorm:
        logging.info(
            f"  restoreNorm={restoreNorm}: bin-width normalization from combine will be restored."
        )
    if merge is None and style is not None:
        merge = extract_mergemap(style)
    if sigs is None:
        sigs = []
    if bkgs is None:
        bkgs = []
    if project is None:
        project = []
    # Fetch hists
    channels = [fitDiag_uproot[f"{fit_shapes_name}/{cat}"] for cat in cats]
    hist_keys = [
        k.split(";")[0]
        for k in channels[0].keys()
        if "data" not in k and "covar" not in k
    ]
    data = getha("data", channels, restoreNorm=restoreNorm)
    hist_dict = geths(
        hist_keys, channels, restoreNorm=restoreNorm, style_dict=None,
    )
    tot_bkg = getha("total_background", channels, restoreNorm=restoreNorm)
    tot = getha("total", channels, restoreNorm=restoreNorm)
    # Prepare merges
    hist_dict = merge_hists(hist_dict, merge)
    _merged_away = []
    for k, v in merge.items():
        _merged_away += v
    # Check if all available
    for key in sigs + bkgs + project:
        if key not in hist_dict.keys():
            raise ValueError(
                f"Hist '{key}' is missing. Available keys are: {hist_keys}"
            )

    # Soft-fail on missing hist
    def hist_dict_fcn(name):
        return hist_dict[name]

    # Remove tiny
    if remove_tiny:
        if isinstance(remove_tiny, str) and remove_tiny.endswith("%"):
            _th = float(remove_tiny[:-1]) * 0.01 * np.sum(data.values())
        elif remove_tiny is True:
            _th = 0.05 * np.sum(data.values())
        elif np.isnumeric(remove_tiny):
            _th = remove_tiny
        else:
            raise ValueError(f"Kwarg `remove_tiny={remove_tiny}` not understood.")
        for key in hist_keys:
            if key in bkgs + sigs + project:
                continue
            if np.sum(hist_dict_fcn(key).values()) < _th:
                logging.info(
                    f"  Skipping hist {key}: because its yield is below threshold."
                )
                hist_keys.remove(key)

    # Fetch keys
    default_signal = [
        k
        for k in hist_keys
        if channels[0][k] == channels[0]["total_signal"] and "total" not in k
    ]
    default_bkgs = [
        k
        for k in hist_keys
        if k not in default_signal and k != onto and "total" not in k
    ]
    _sortable, _extra = (
        [k for k in default_bkgs if k in style.keys()],
        [k for k in default_bkgs if k not in style.keys()],
    )
    default_bkgs = ([k for k in style.keys() if k in _sortable] + _extra)[::-1]
    if len(bkgs) == 0:
        bkgs = default_bkgs
    if len(sigs) > 2:
        raise ValueErrors(
            "Are you insane? More than 2 signal? Write your own plotter lol."
        )
    elif len(sigs) == 0:
        sigs = default_signal
    bkgs = [bkg for bkg in bkgs if bkg != onto and bkg not in sigs]
    # Remove negatives from backgrounds/stackable:
    sigs_ratio = sigs.copy()  # Allow negatives in ratio
    for sg in [sigs, bkgs]:
        for key in sg:
            if np.any(hist_dict_fcn(key).values() < 0):
                logging.warning(
                    f"  Hist {key} has negative values and will not be show in the stack"
                )
                logging.debug(f"  Hist {key}: {hist_dict_fcn(key).values()}")
                sg.remove(key)
    logging.info(f"  Signals: {','.join(sigs)}.")
    logging.info(f"  Backgrounds: {','.join(bkgs)}.")
    logging.info(f"  Onto bkg: {onto}.")
    unused = [
        key
        for key in hist_keys
        if key not in sigs + bkgs + project + [onto] and "total" not in key and key not in _merged_away
    ]
    if len(unused) > 0:
        logging.warning(
            f"Samples: {unused} are available in the workspace, but not included to be plotted."
        )
    for key in sigs + bkgs:
        if key not in style.keys():
            logging.warning(
                f"  Key `{key} is not available in `styles`. Will autofill",
            )
            style[key] = {"label": key}
    style = fill_colors(style, cmap=cmap10, no_duplicates=False)
    logging.debug(f"  Style: \n{log_pretty(style)}")

    ###############
    # Plotting main
    fig, (ax, rax) = plt.subplots(
        2, 1, gridspec_kw={"height_ratios": (3, 1)}, sharex=True
    )
    plt.subplots_adjust(hspace=0)
    if onto is None:
        hep.histplot(
            [hist_dict_fcn(k) for k in bkgs + sigs],
            ax=ax,
            label=bkgs + sigs,
            stack=True,
            histtype="fill",
            facecolor=[style[k]["color"] for k in bkgs + sigs],
        )
    else:
        hep.histplot(
            hist_dict_fcn(onto),
            ax=ax,
            label="qcd",
            yerr=False,  # facecolor='none',
            histtype="step",
            color=style["qcd"]["color"],  # hatch=style['qcd']['hatch'],
            lw=2,
        )
        hep.histplot(
            [hist_dict[onto], *[hist_dict_fcn(k) for k in bkgs + sigs]],
            ax=ax,
            label=["_", *(bkgs + sigs)],
            stack=True,
            histtype="fill",
            facecolor=["none", *[style[k]["color"] for k in bkgs + sigs]],
        )
    hep.histplot(
        data, ax=ax, label="data", xerr=True, histtype="errorbar", color="k", zorder=4
    )

    # Ploting projection
    if len(project) != 0:
        logging.info(f"  Projecting on x-axis: {','.join(project)}")
        hep.histplot(
            [hist_dict_fcn(k) for k in project],
            ax=ax,
            facecolor=[style[k]["color"] for k in project],
            stack=True,
            histtype="fill",
        )

    # Project signal
    if rmap is None:
        if len(sigs) == 1:
            rmap = {sigs[0]: "r"}
    if project_signal is not None:
        _rs = dict(zip(sigs, [1] * len(sigs)))
        if fitDiag_root is None and "prefit" not in fit_type:
            logging.warning(
                "Kwarg `fitDiag_root` was not passed. Postfit signal strengths are unavailable. "
                "Kwarg `project_signal` will be scaling the postfit distribution: `nominal * r * project_signal`. "
                "When `fitDiag_root` is available, signal strength gets factored out resulting in: `nominal * project_signal`."
            )
        else:
            if fitDiag_root is not None and rmap is None:
                raise ValueError(
                    "Cannot infer sample:poi mapping for more than 1 signal. Pass e.g. "
                    "rmap={'hbb': 'r', 'hcc':'r2'}"
                )
            else:
                _rs = {
                    sig: get_fit_val(
                        fitDiag_root, rmap[sig], fittype=fit_type, substitute=1.0
                    )
                    for sig in rmap
                }
        sig_dicts = defaultdict(lambda: 1)
        for sig, proj in zip(sigs, project_signal):
            sig_dicts[sig] = proj
        logging.info(
            f"  Projecting signal on x-axis: {'; '.join([f'{k}:{v:.2f}' for k, v in _rs.items()])}"
        )
        for sig in sigs:
            _scaled_sig = hist_dict_fcn(sig) * sig_dicts[sig] / _rs[sig]
            _p_label = (
                style[sig]["label"]
                if sig_dicts[sig] == 1
                else f"{style[sig]['label']} x {sig_dicts[sig]:.0f}"
            )
            hep.histplot(
                _scaled_sig,
                ax=ax,
                color=style[sig]["color"],
                stack=True,
                histtype="step",
                label=_p_label,
                yerr=False,
                ls="--",
                lw=2,
            )

    #########
    # Subplot
    rh = (data.values() - tot_bkg.values()) / np.sqrt(data.variances())
    ## Plotting subplot
    hep.histplot(
        rh,
        data.axes[0].edges,
        ax=rax,
        yerr=1,
        histtype="errorbar",
        color="k",
        xerr=True,
        zorder=4,
    )
    #     hep.histplot(tot_sig/np.sqrt(data.variances()), ax=rax,
    #                  color=style['total_signal']['color'], lw=2,
    #                  label='Signal',
    #                 )
    hep.histplot(
        [hist_dict_fcn(sig) / np.sqrt(data.variances()) for sig in sigs_ratio],
        ax=rax,
        color=[style[sig]["color"] for sig in sigs_ratio],
        stack=True,
        histtype="fill",
        label=[style[sig]["label"] for sig in sigs_ratio],
    )
    ## Bkg Unc
    yerr_nom = np.sqrt(tot_bkg.variances() * tot_bkg.axes[0].widths) / np.sqrt(
        data.variances() * tot_bkg.axes[0].widths
    )
    yerr = yerr_nom.copy()
    yerr[~np.isfinite(yerr_nom)] = 0
    err_th = np.max([7, 1.5 * np.max(abs(np.r_[0.01, rh[np.isfinite(rh)]]))])
    good_yerr_mask = yerr < err_th  # Data unc is 1 by definiton
    yerr[~good_yerr_mask] = 0
    hep.histplot(
        np.zeros_like(data.values()),
        tot_bkg.axes[0].edges,
        yerr=[yerr, yerr],
        histtype="band",
        label="Bkg. Unc.",
        zorder=-1,
    )

    if np.sum(~good_yerr_mask) > 1:
        logging.warning(
            f"  Bkg. Unc. in {np.sum(~good_yerr_mask)} bins is too large ( > err_th) and will be set to 0. Full uncertainty is: {yerr_nom}"
        )

    #########
    # Styling
    ax.legend(ncol=2)

    # Axis limits
    if clipx:
        _h, _bins = data.to_numpy()
        _h += tot_bkg.to_numpy()[0]
        nonzero = _bins[:-1][_h > 0]
        ax.set_xlim(nonzero[0], nonzero[-1])
    else:
        ax.set_xlim(data.axes[0].edges[0], data.axes[0].edges[-1])

    # Axis labels
    ax.set_xlabel(None)
    rax.set_xlabel(tot_bkg.axes[0].label)
    if restoreNorm:
        if np.std(data.axes[0].widths) == 0:
            _binwidth = f"{np.mean(data.axes[0].widths):.0f}"
        else:
            _binwidth = f"{stats.mode(np.mean(data.axes[0].widths)).mode:.0f}"
            logging.warning(
                "  Bin-width is not constant. Consider setting custom y-label"
            )
        ax.set_ylabel(f"Events / {_binwidth}GeV")
    else:
        ax.set_ylabel("Events / GeV")

    # Ratio
    rax.legend(
        loc="upper right",
        ncol=3,
        markerscale=0.8,
        fontsize="small",
        labelspacing=0.4,
        columnspacing=1.5,
    )
    #     handles, labels = rax.get_legend_handles_labels()
    #     rax.legend(reversed(handles), reversed(labels), loc='upper right', ncol=2)
    limlo, limhi = rax.get_ylim()
    rax.set_ylim(np.min([-2, limlo]), np.max([2, limhi * 1.8]))
    hep.yscale_legend(rax)
    rax.axhline(0, color="gray", ls="--")
    rax.set_ylabel(r"$\frac{Data-Bkg}{\sigma_{Data}}$", y=0.5)

    # Reformatting legend
    existing_keys = ax.get_legend_handles_labels()[-1]
    for key in existing_keys:
        if key not in style.keys():
            style[key] = {"label": key}
    order = np.argsort([list(style.keys()).index(i) for i in existing_keys])
    handles, labels = ax.get_legend_handles_labels()
    handles = [handles[i] for i in order]
    labels = [style[labels[i]]["label"] for i in order]
    leg = format_legend(
        ax,
        ncols=2,
        handles_labels=(handles, labels),
        bbox_to_anchor=(1, 1),
        markerscale=0.8,
        fontsize="small",
        labelspacing=0.4,
        columnspacing=1.5,
    )
    hep.yscale_legend(ax)
    if fit_type == "prefit":
        leg.set_title(title=fit_type.capitalize(), prop={"size": "small"})
    else:
        # Don't write postfit to save space, just print r
        if fitDiag_root is None:
            leg.set_title(title="Postfit", prop={"size": "small"})
        else:
            # Write signal strengths
            leg.set_title(title=None, prop={"size": "small"})
            fig.canvas.draw()
            mu_strs = []
            for sig in sigs:
                _r = get_fit_val(
                    fitDiag_root, rmap[sig], fittype=fit_type, substitute=1.0
                )
                _r = rf"{_r:.2f}"
                _d, _u = get_fit_unc(
                    fitDiag_root, rmap[sig], fittype=fit_type, substitute=1.0
                )
                _d, _u = rf"{_d:.2f}", f"{_u:.2f}"
                mu_strs.append(
                    r"$\mu_{%s}$ = " % style[sig]["label"].replace("$", "")
                    + r"${%s}_{%s}^{%s}$" % (_r, _d, _u)
                )

            fig.canvas.draw()
            bbox = leg.get_window_extent().transformed(ax.transAxes.inverted())
            x, y = bbox.xmin + bbox.width / 2, bbox.ymin
            ax.text(
                x,
                y,
                "  ".join(mu_strs),
                fontsize="x-small",
                ha="center",
                va="top",
                transform=ax.transAxes,
            )
            ax.set_ylim(None, ax.get_ylim()[-1] * 1.05)

    if cat_info:
        from matplotlib.offsetbox import AnchoredText

        at = AnchoredText(
            f"Categories: \n{format_categories(cats, cat_info)}",
            loc="upper left",
            pad=0.8,
            prop=dict(size="x-small", ha="center"),
            frameon=False,
        )
        ax.add_artist(at)
        hep.plot.yscale_anchored_text(ax)

    if chi2:
        chi2_val = np.sum(
            np.nan_to_num(
                abs(data.values() - tot.values()) / data.variances(), posinf=0, neginf=0
            )
        )
        # Should be just a bit higher than 'saturated'
        at = AnchoredText(
            rf"$\chi^2$ = {chi2_val:.2f}",
            loc="upper left",  # pad=0.8,
            prop=dict(size="x-small", ha="center"),
            frameon=False,
        )
        rax.add_artist(at)
        hep.plot.yscale_anchored_text(rax)

    return fig, (ax, rax)
