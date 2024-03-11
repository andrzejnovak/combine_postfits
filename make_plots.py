import os
import ROOT as r
import uproot
import logging
import yaml
import matplotlib
from multiprocessing import Process
import copy

matplotlib.use("Agg")
import mplhep as hep
import argparse

from combine_postfits import plot, utils

hep.style.use("CMS")

if __name__ == "__main__":

    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ("yes", "true", "t", "y", "1"):
            return True
        elif v.lower() in ("no", "false", "f", "n", "0"):
            return False
        else:
            raise argparse.ArgumentTypeError("Boolean value expected.")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input", default="fitDiagnosticsTest.root", help="Input shapes file"
    )
    parser.add_argument(
        "--fit",
        default="all",
        choices={"prefit", "fit_s", "all"},
        dest="fit",
        help="Shapes to plot",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        default="plots",
        dest="output_folder",
        help="Folder to store plots - will be created if it doesn't exist.",
    )
    parser.add_argument(
        "--year",
        default=None,
        choices={"2016", "2017", "2018", ""},
        type=str,
        help="year label",
    )
    parser.add_argument(
        "-s",
        "--style",
        default=None,
        dest="style",
        help="Style file yaml e.g. `style.yml`",
    )
    parser.add_argument(
        "--sigs",
        default=None,
        dest="sigs",
        help="Comma-separated list of keys available in provided `--style sty.yml` file, e.g. `ggH,VBF`",
    )
    parser.add_argument(
        "--project-signals",
        "--project_signals",
        default=None,
        dest="project_signals",
        help="Comma-separated list of values of equal length with --sigs, e.g. `1,1`",
    )
    parser.add_argument(
        "--bkgs",
        default=None,
        dest="bkgs",
        help="Comma-separated list of keys available in provided `--style sty.yml` file, e.g. `ggH,VBF`",
    )
    parser.add_argument(
        "--onto",
        default=None,
        dest="onto",
        help="Bkg to plot other processes onto, e.g. `qcd`.",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="png",
        choices={"png", "pdf", "both"},
        help="Plot format",
    )
    parser.add_argument(
        "--cmap",
        type=str,
        default=None,
        help="Name of `cmap` to fill colors in `style.yml` from. Eg.: Tiepolo;Renoir;tab10",
    )

    pseudo = parser.add_mutually_exclusive_group(required=True)
    pseudo.add_argument("--data", action="store_false", dest="pseudo")
    pseudo.add_argument("--MC", action="store_true", dest="pseudo")
    pseudo.add_argument("--toys", action="store_true", dest="toys")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--debug", "-vv", action="store_true", help="Debug logging")
    parser.add_argument("-p", action="store_true", dest='multiprocessing', help="Use multiprocessing to make plots. May fail due to parallel reads from fitDiag.")
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    # Arg processing
    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    if args.fit == "all":
        fit_types = ["prefit", "fit_s"]
    else:
        fit_types = [args.fit]
    if args.format == "both":
        format = ["png", "pdf"]
    else:
        format = [args.format]

    # Make plots
    fd = uproot.open(args.input)
    rfd = r.TFile.Open(args.input)
    if args.style is not None:
        with open(args.style, "r") as stream:
            try:
                style = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    else:
        style = utils.make_style_dict_yaml(fd, cmap=args.cmap)
        logging.warning(
            "No `--style sty.yml` file provided, will generate an automatic style yaml and store it as `sty.yml`. "
            "The `plot` function will respect the order of samples in the style yaml unless overwritten. "
            "\nTo pass LaTeX expressions to 'label' use single quotes eg. '$H_{125}(\\tau\\bar{\\tau})$'"
        )
        with open("sty.yml", "w") as outfile:
            yaml.dump(style, outfile, default_flow_style=False, sort_keys=False)

    if args.pseudo and args.toys:
        style["data"]["label"] = "Toys"
    elif args.pseudo and not args.toys:
        style["data"]["label"] = "MC"
    else:
        style["data"]["label"] = "Data"

    for fit_type in fit_types:
        channels = [
            c[:-2] for c in fd[f"shapes_{fit_type}"].keys() if c.count("/") == 0
        ]
        for channel in channels:
            # Wrap it in a function to enable parallel processing
            def mod_plot():
                fig, (ax, rax) = plot.plot(
                    fd,
                    fit_type,
                    sigs=args.sigs.split(",") if args.sigs else None,
                    bkgs=args.bkgs.split(",") if args.bkgs else None,
                    onto=args.onto,
                    project_signal=[float(v) for v in args.project_signals.split(",")] if args.project_signals else None,
                    cats=[channel],
                    restoreNorm=True,
                    clipx=True,
                    fitDiag_root=rfd,
                    style=style,
                    cat_info=1,
                    chi2=True,
                )
                rax.set_xlabel(r"$m_{\tau\bar{\tau}}^{reg}$")
                hep.cms.label("Private Work", data=not args.pseudo, ax=ax)
                for fmt in format:
                    fig.savefig(
                        f"{args.output_folder}/{channel}_{fit_type}.{fmt}", format=fmt
                    )
                
            p = Process(target=mod_plot)
            p.start()
            if not args.multiprocessing:
                p.join()
            
            
            
    
