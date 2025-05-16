import matplotlib
# matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import List, Union, Optional
from typeguard import typechecked
import logging
import numpy as np
from matplotlib.offsetbox import AnchoredText
import mplhep as hep
import hist

np.seterr(divide="ignore", invalid="ignore")

import hist
from typing import List, Union
import fnmatch
import itertools

@typechecked
def plot_cov(
    fitDiagnostics_file: str = "fitDiagnostics.root",
    fit_type: str = "fit_s",  # 'prefit' | 'fit_s' | 'fit_b'
    include: Union[str, List[str], None] = None,
    exclude: Union[str, List[str], None] = "*mcstat*",
    tick_rotation: int = 30,
    cmap="RdBu",
) -> Optional[plt.Axes]:
    logging.info(f"Plotting covariance matrix from {fitDiagnostics_file} ({fit_type})")
    import ROOT as r

    rf = r.TFile.Open(fitDiagnostics_file)
    h2 = rf.Get(fit_type).correlationHist()
    
    x_bins = h2.GetXaxis().GetNbins()
    y_bins = h2.GetYaxis().GetNbins()
    y_labels = [h2.GetYaxis().GetBinLabel(i) for i in range(1, y_bins + 1)]
    x_labels = [h2.GetXaxis().GetBinLabel(i) for i in range(1, x_bins + 1)]
    hist_2d = hist.new.StrCat(x_labels, label="").StrCat(y_labels, label="").Double()
    for i in range(0, x_bins):
        for j in range(0, y_bins):
            hist_2d.view()[i, j] = h2.GetBinContent(i + 1, j + 1)

    keys = x_labels
    if isinstance(include, str) or isinstance(include, list):
        if not isinstance(include, list):
            include = [include]
        if any(any(special in pattern for special in ["*", "?"]) for pattern in include):
            keys = []
            for pattern in include:
                keys.append([k for k in x_labels if fnmatch.fnmatch(k, pattern)])
            keys = list(dict.fromkeys(list(itertools.chain.from_iterable(keys))))
        else:
            keys = include
    logging.debug(f"  --include {len(keys)} / {len(x_labels)} keys: {keys if len(keys) < 10 else keys[:5] + ['...']}")

    if exclude is not None:
        if not isinstance(exclude, list):
            exclude = [exclude]
        exclude_keys = []
        for pattern in exclude:
            exclude_keys.append([k for k in x_labels if fnmatch.fnmatch(k, pattern)])
        exclude_keys = list(dict.fromkeys(list(itertools.chain.from_iterable(exclude_keys))))
        keys = [k for k in keys if k not in exclude_keys]      
        logging.debug(f"  --exclude {len(exclude_keys)} / {len(x_labels)} keys: {exclude_keys if len(exclude_keys) < 10 else exclude_keys[:5] + ['...']}")
    assert len(keys) > 0, "No keys left after filtering. Check your include/exclude patterns."
    logging.info(f"  Plotting {len(keys)} / {len(x_labels)} keys: {keys if len(keys) < 10 else keys[:5] + ['...']}")
    if "r" in keys:  # put signal at the beginning
        keys.remove("r")
        keys = ["r"] + keys

    # Plot it
    fig, ax = plt.subplots()
    hist_2d[keys, keys].plot2d(cmap=cmap, cmin=-1, cmax=1, ax=ax)
    _base_fontsize = plt.rcParams['font.size']
    from matplotlib.font_manager import font_scalings 
    _base_fontsize = font_scalings.get('small') * _base_fontsize      
    _fontsize = max(6, min(_base_fontsize, 24 - 0.25 * len(keys)))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=tick_rotation, horizontalalignment="right", fontsize=_fontsize)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=tick_rotation, horizontalalignment="right", fontsize=_fontsize)
    ax.minorticks_off()
    ax.set_ylabel("")
    ax.set_xlabel("")

    return ax


def main():
    import matplotlib
    matplotlib.use("Agg")
    import argparse
    import click
    from rich.logging import RichHandler
    from rich_argparse_plus import RichHelpFormatterPlus
    RichHelpFormatterPlus.styles["argparse.syntax"] = "#88C0D0"

    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatterPlus)
    parser.add_argument(
        "--input",
        "-i",
        default="fitDiagnosticsTest.root",
        help="Input combine fitDiagnostics file",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="plots",
        dest="output",
        help="Output folder (will becreated if it doesn't exist). Can set absolute path to file, will overwrite `--format`.",
    )
    parser.add_argument(
        "--fit",
        default="fit_s",
        choices=["fit_s", "fit_b"],
        dest="fit",
        help="Shape set to plot.",
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        default="png",
        choices=["png", "pdf", "both"],
        help="Plot output format",
    )
    parser.add_argument(
        "--include",
        type=str,
        default=None,
        help="Comma-separated list of nuisances to be included in the plot. Can use wildcards. "\
             "Non-matching nuisances will be excluded. If not set, all nuisances will be included.",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default="*mcstat*",
        help="Comma-separated list of nuisances to be excluded in the plot. Can use wildcards. "\
             "By default `*mcstat*` is excluded. Pass empty string to include all nuisances.",
    )
    parser_data = parser.add_argument_group(
        "Data",
        description="Data/MC Fit label.",
    )
    pseudo = parser_data.add_mutually_exclusive_group(required=True)
    pseudo.add_argument("--data", action="store_false", dest="pseudo")
    pseudo.add_argument("--MC", action="store_true", dest="pseudo")
    
    
    parser_styling = parser.add_argument_group("Styling")
    parser_styling.add_argument(
        "--cmap",
        type=str,
        default="RdBu",
        help="Name of a matplotlib/seaborn cmap.",
    )
    parser_styling.add_argument(
        "--cmslabel",
        default="Private Work",
        type=str,
        help="CMS Label",
    )
    parser_styling.add_argument(
        "--com",
        "--center-of-mass",
        default="13",
        type=str,
        help="C-o-M label. Eg. `13` (TeV)",
    )
    parser_styling.add_argument(
        "--year",
        default=None,
        type=str,
        help="Year label. Eg. '2017' or 'Run2' or '2022+2023'",
    )
    parser_styling.add_argument(
        "--pub",
        default=None,
        type=str,
        help="Supplementary label - arxiv no.",
    )
    parser_styling.add_argument(
        "--dpi",
        default=300,
        type=int,
        help="DPI for png format.",
    )
    parser_debug = parser.add_argument_group("DEBUG Options")
    parser_debug.add_argument(
        "--verbose", "-v", "-_v", action="store_true", help="Verbose logging"
    )
    parser_debug.add_argument(
        "--debug", "-vv", "--vv", action="store_true", help="Debug logging"
    )
   
    import textwrap

    epilog = textwrap.dedent(
    """
    Minimal example:
    ```
    #combine_postfits -i fitDiagnosticsTest.root --data
    ```
    """
    )
    parser_epi = parser.add_argument_group("Examples:", description=epilog)

    args = parser.parse_args()

    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("fsspec").setLevel(logging.WARNING)
    logging.getLogger("ROOT").setLevel(logging.WARNING)
    logging.getLogger("boost_histogram").setLevel(logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click])],
    )

    import os
    os.makedirs(args.output, exist_ok=True)

    hep.style.use("CMS")

    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore",category=UserWarning, module="hist")

        ax = plot_cov(
            args.input,
            args.fit,
            include=args.include.split(",") if args.include else None,
            exclude=args.exclude.split(",") if args.exclude else None,
            cmap=args.cmap,
        )
    
    fig = ax.figure
    hep.cms.label(ax=ax, data=args.pseudo, year=args.year, label=args.cmslabel, pub=args.pub, com=args.com)

    full_path = args.output if args.output.endswith(".png") or args.output.endswith(".pdf") else None
    if full_path is None:
        full_path = os.path.join(args.output, f"cov_{args.fit}._format_")
    formats = ["png", "pdf"] if args.format == "both" else [args.format]
    for fmt in formats:
        fig.savefig(full_path.replace("_format_", fmt), dpi=args.dpi, bbox_inches="tight")
        logging.info(f"Saved covariance plot to {full_path.replace('_format_', fmt)}")


if __name__ == "__main__":
    main()