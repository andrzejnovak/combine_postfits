import os
import ROOT as r
import uproot
import logging
import yaml
import matplotlib
from multiprocessing import Process, Semaphore
import tqdm
import time
import copy

matplotlib.use("Agg")
import mplhep as hep
import argparse

from combine_postfits import plot, utils

import click
import logging
from rich.logging import RichHandler
from rich.progress import Progress, TextColumn, BarColumn, MofNCompleteColumn, TimeRemainingColumn, TimeElapsedColumn

hep.style.use("CMS")

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")

def main():
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
        "--cats",
        default=None,
        dest="cats",
        help="Either a comma-separated list of categories to plot or a mapping of categories to plot together, e.g. `cat1,cat2` in the form of `mcat1:cat1,cat2;mcat2:cat3,cat4`",
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
    # Styling/Colors
    parser.add_argument(
        "-s",
        "--style",
        default=None,
        dest="style",
        help="Style file yaml e.g. `style.yml`",
    )
    parser.add_argument(
        "--cmap",
        type=str,
        default=None,
        help="Name of `cmap` to fill colors in `style.yml` from. Eg.: Tiepolo;Renoir;tab10",
    )
    parser.add_argument("--clipx",
        type=str2bool,
        default='True',
        choices={True, False},
        help="Clip x-axis to range of data",
    )

    # Labels
    pseudo = parser.add_mutually_exclusive_group(required=True)
    pseudo.add_argument("--data", action="store_false", dest="pseudo")
    pseudo.add_argument("--MC", action="store_true", dest="pseudo")
    pseudo.add_argument("--toys", action="store_true", dest="toys")
    parser.add_argument(
        "--blind",
        type=str,
        default=None,
        help="Category to blind data (not plotted), e.g. `cat1`",
    )
    parser.add_argument(
        "--year",
        default=None,
        choices={"2016", "2017", "2018", ""},
        type=str,
        help="year label",
    )
    parser.add_argument(
        "--lumi",
        default=None,
        type=float,
        help="Luminosity for label",
    )
    parser.add_argument(
        "--pub",
        default=None,
        type=str,
        help="arxiv no",
    )
    parser.add_argument(
        "--xlabel",
        default=r'$m_{\tau\bar{\tau}}^{reg}$',
        type=str,
        help="Plot x-label. If left `None` will read from combine. When using latex enclose string as 'str'.",
    )
    parser.add_argument(
        "--ylabel",
        default=None,
        type=str,
        help="Plot y-label. If left `None` will read from combine. When using latex enclose string as 'str'.",
    )
    parser.add_argument(
        "--cmslabel",
        default="Private Work",
        type=str,
        help="CMS Label",
    )

    # Debug
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
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click])]
    )

    if args.fit == "all":
        fit_types = ["prefit", "fit_s"]
    else:
        fit_types = [args.fit]
    for fit in fit_types:
        os.makedirs(f"{args.output_folder}/{fit}", exist_ok=True)
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

    if args.blind is not None:
        blind_cats = args.blind.split(",") if "," in args.blind else [args.blind]
    else:
        blind_cats = []
        
    # Get types/cats/blinds unwrapped
    all_channels = []
    all_blinds = []
    all_types = []
    all_savenames = []
    for fit_type in fit_types:
        if args.cats is None:
            channels = [
                [c[:-2]] for c in fd[f"shapes_{fit_type}"].keys() if c.count("/") == 0
            ]
            blinds = [True if c[0] in blind_cats else False for c in channels]
            savenames = [c[0] for c in channels]
        else:
            if ":" in args.cats:
                channels = []
                blinds = []
                savenames = []
                for cat in args.cats.split(";"):
                    mcat, cats = cat.split(":")
                    channels.append(cats.split(","))
                    blinds.append(True if mcat in blind_cats else False)
                    savenames.append(mcat)
            else:
                channels = [[c] for c in args.cats.split(",")]
                blinds = [True if c in blind_cats else False for c in args.cats.split(",")]
                savenames = args.cats.split(",")
        assert isinstance(channels[0], list)
        all_channels.extend(channels)
        all_blinds.extend(blinds)
        all_types.extend([fit_type] * len(channels))   
        all_savenames.extend(savenames)
        
    _procs = []
    with Progress(TextColumn("[progress.description]{task.description}"), BarColumn(), MofNCompleteColumn(), TimeRemainingColumn(), TimeElapsedColumn(),) as progress:
        prog_str = f"[red]Plotting (parallel): " if args.multiprocessing else f"[red]Plotting: "
        prog_plotting = progress.add_task(prog_str, total=len(all_channels))
        semaphore = Semaphore(20 if args.multiprocessing else 0)
        for fittype, channel, blind, sname in zip(all_types, all_channels, all_blinds, all_savenames):
            # Wrap it in a function to enable parallel processing
            def mod_plot(semaphore=None):
                fig, (ax, rax) = plot.plot(
                    fd,
                    fittype,
                    sigs=args.sigs.split(",") if args.sigs else None,
                    bkgs=args.bkgs.split(",") if args.bkgs else None,
                    onto=args.onto,
                    project_signal=[float(v) for v in args.project_signals.split(",")] if args.project_signals else None,
                    blind=blind,
                    cats=channel,
                    restoreNorm=True,
                    clipx=args.clipx,
                    fitDiag_root=rfd,
                    style=style,
                    cat_info=1,
                    chi2=True,
                )
                if args.xlabel is not None:
                    rax.set_xlabel(args.xlabel)
                if args.ylabel is not None:
                    rax.set_ylabel(args.xlabel)
                hep.cms.label(args.cmslabel, data=not args.pseudo, ax=ax, lumi=args.lumi, pub=args.pub, year=args.year) 
                for fmt in format:
                    fig.savefig(
                        f"{args.output_folder}/{fittype}/{sname}_{fittype}.{fmt}", format=fmt
                    )
                if semaphore is not None:
                    semaphore.release()
            
            if args.multiprocessing:
                semaphore.acquire()
                p = Process(target=mod_plot, args=(semaphore, ))
                _procs.append(p)
                p.start()
                time.sleep(0.5)
            else:
                mod_plot()
                progress.update(prog_plotting, advance=1, refresh=True)

        if args.multiprocessing:
            while sum([p.is_alive() for p in _procs]) > 0:
                n_running = sum([p.is_alive() for p in _procs])    
                progress.update(prog_plotting, completed=len(_procs) - n_running, refresh=True)
                time.sleep(0.1)
        progress.update(prog_plotting, completed=len(_procs), refresh=True)

if __name__ == "__main__":
    main()