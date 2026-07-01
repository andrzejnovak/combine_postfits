import argparse
import fnmatch
import importlib.util
import logging
import sys
import time
from dataclasses import dataclass
from multiprocessing import Process, Semaphore
from pathlib import Path
from typing import Any, Iterator

import matplotlib
import mplhep as hep
import numpy as np
import uproot
import yaml
from rich.prompt import Confirm
from rich_argparse_plus import RichHelpFormatterPlus

RichHelpFormatterPlus.styles["argparse.syntax"] = "#88C0D0"
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.traceback import install

from combine_postfits import plot_postfits, utils
from combine_postfits.utils import str2bool

install(show_locals=False)

ROOT_spec = importlib.util.find_spec("ROOT")
ROOT_AVAILABLE = ROOT_spec is not None
if ROOT_AVAILABLE:
    import ROOT as r

hep.style.use("CMS")


def time_check(progress: Progress, procs: list[Process], limit: int = 5) -> None:
    """Monitor plotting processes and terminate if they exceed the time limit."""
    if progress.tasks[0].elapsed // 60 >= limit:
        logging.error(
            f"Plotting taking longer than {limit} minutes. Likely and issue with file opening or too many figures. Try rerunning or running with `--p 0`."
        )
        remaining_procs = [p for p in procs if p.is_alive()]
        logging.error(f"Terminating remaining plot processes: {[p.name for p in remaining_procs]}")
        for p in remaining_procs:
            p.terminate()
        import sys

        sys.exit()


def sci_notation(number: float, sig_fig: int = 1, no_zero: bool = False) -> str:
    """Format a number in scientific notation for LaTeX (e.g. 1.2 x 10^{3})."""
    ret_string = f"{number:.{sig_fig}e}"
    a, b = ret_string.split("e")
    b = int(b)
    if float(a) == 0:
        return r"\ " if no_zero else "0"
    elif float(a) == 1:
        return f"10^{{{b}}}"
    else:
        return rf"{a}\,x\,10^{{{b}}}"


def get_digits(number: float) -> tuple[int, int]:
    """Return the number of digits before and after the decimal point."""
    before, _, after = np.round(number, 10).astype(str).partition(".")
    return len(before), len(after)


@dataclass
class PlotTask:
    """Encapsulates all parameters needed for a single plot job."""

    fittype: str
    channels: list[str]
    blind: bool
    savename: str
    label: str | None
    blind_range: str | None


def generate_plot_tasks(
    args: argparse.Namespace, fit_types: list[str], fd: uproot.ReadOnlyDirectory
) -> Iterator[PlotTask]:
    """Generate PlotTask objects based on CLI arguments and available channels."""
    # 1. Parse Blinding Patterns
    if args.blind is not None:
        blind_cat_patterns = args.blind.split(",") if "," in args.blind else [args.blind]
    else:
        blind_cat_patterns = []
    logging.debug(f"Blind categories matching: {blind_cat_patterns}")

    # 2. Parse Blind Data Ranges
    blind_mapping = {}
    if args.blind_data is not None:
        for _mapping in args.blind_data.split(";"):
            if ":" not in _mapping:
                logging.error(f"Invalid blind-data mapping '{_mapping}', expected 'category:range'. Skipping.")
                continue
            cat_pattern, slice_string = _mapping.split(":", 1)
            blind_mapping[cat_pattern] = slice_string
        logging.debug(f"Blind data mapping:\n{blind_mapping}")

    # 3. Parse rmap (signal mapping)
    # (Note: rmap validation logic remains in main() or can be moved here if it affects task generation.
    # Currently it mostly affects plotting, so we leave it, but args.rmap is used for validation.)

    for fit_type in fit_types:
        # Get available channels for this fit type
        # Shapes are like "shapes_prefit/channel/sample", we want "channel"
        # We filter out typical ROOT subdirectories or non-channel keys if necessary
        available_channels = [c.split(";")[0] for c in fd[f"shapes_{fit_type}"].keys() if c.count("/") == 0]
        logging.debug(f"Available '{fit_type}' channels: {available_channels}")

        # Resolve which channels are blinded
        blind_cats = set()
        for pattern in blind_cat_patterns:
            blind_cats.update(fnmatch.filter(available_channels, pattern))
            # Also check against merged category names if --cats is used
            if args.cats:
                cat_names = [catmap.split(":")[0] for catmap in args.cats.split(";")]
                blind_cats.update(fnmatch.filter(cat_names, pattern))
        logging.debug(f"Categories to blind: {blind_cats}")

        # Resolve blind ranges per channel
        # We flatten the mapping: {channel: "range_string"}
        blind_mapping_flattened = {}
        if args.blind_data:
            target_channels = (
                [catmap.split(":")[0] for catmap in args.cats.split(";")] if args.cats else available_channels
            )
            for pattern, slice_string in blind_mapping.items():
                for channel in fnmatch.filter(target_channels, pattern):
                    blind_mapping_flattened[channel] = slice_string
            logging.debug(f"Blind mapping flattened: {blind_mapping_flattened}")

        # Generate Tasks
        # Case A: Implicitly plot all available channels
        if args.cats is None:
            logging.debug(f"Plotting all channels: {available_channels}")
            for channel in available_channels:
                yield PlotTask(
                    fittype=fit_type,
                    channels=[channel],
                    blind=(channel in blind_cats),
                    savename=channel,
                    label=None,  # Will be autofilled later or used as is
                    blind_range=blind_mapping_flattened.get(channel),
                )

        # Case B: Standard list of categories (comma-sep) or Merged categories (colon-sep)
        else:
            # We enforce semicolon separator for clarity in complex args, but logic follows original
            # "cat1,cat2" -> list of separate plots
            # "merged:cat1,cat2" -> one plot summing cat1 and cat2
            if ":" in args.cats:
                # Mapping mode: "name:cat1,cat2; name2:cat3"
                for cat_group in args.cats.split(";"):
                    if ":" not in cat_group:
                        logging.warning(
                            f"Skipping malformed category mapping '{cat_group}'. Expected format 'name:cat1,cat2'"
                        )
                        continue
                    mcat, pat_list = cat_group.split(":", 1)
                    # Resolve wildcards in the pattern list
                    resolved_cats = []
                    for pat in pat_list.split(","):
                        resolved_cats.extend(fnmatch.filter(available_channels, pat))

                    if not resolved_cats:
                        logging.warning(f"No channels found matching '{pat_list}' for group '{mcat}'")
                        continue

                    yield PlotTask(
                        fittype=fit_type,
                        channels=resolved_cats,
                        blind=(mcat in blind_cats),
                        savename=mcat,
                        label=args.catlabels if args.catlabels and ";" not in args.catlabels else mcat,
                        blind_range=blind_mapping_flattened.get(mcat),
                    )
            else:
                # List mode: "cat1,cat2,cat3" -> 3 plots
                for pat in args.cats.split(","):
                    resolved_cats = fnmatch.filter(available_channels, pat)
                    for channel in resolved_cats:
                        yield PlotTask(
                            fittype=fit_type,
                            channels=[channel],
                            blind=(channel in blind_cats),
                            savename=channel,
                            label=None,
                            blind_range=blind_mapping_flattened.get(channel),
                        )


def process_plot(
    semaphore,
    fd: uproot.ReadOnlyDirectory,
    rfd: Any,
    task: PlotTask,
    style: dict,
    rmap: dict,
    args: argparse.Namespace,
    out_dir: Path,
    format_list: list[str],
) -> None:
    """Process a single plot task (worker function)."""
    try:
        config = plot_postfits.PlotConfig(
            fit_type=task.fittype,
            cats=task.channels,
            sigs=args.sigs.split(",") if args.sigs else None,
            bkgs=args.bkgs.split(",") if args.bkgs else None,
            onto=args.onto,
            project_signal=([float(v) for v in args.project_signals.split(",")] if args.project_signals else None),
            blind=task.blind,
            blind_data=task.blind_range,
            restoreNorm=True,
            rmap=rmap,
            clipx=args.clipx,
            cat_info=task.label,
            chi2=args.chi2,
            chi2_nocorr=args.chi2_nocorr,
            residuals=args.residuals,
        )
        fig, (ax, rax) = plot_postfits.plot(
            fd,
            config,
            style=style,
            fitDiag_root=rfd,
        )
        if fig is None:
            return None
        # Styling
        if args.xlabel is not None:
            rax.set_xlabel(args.xlabel)
        if args.ylabel is not None:
            ax.set_ylabel(args.ylabel)
        hep.cms.label(
            args.cmslabel,
            data=not args.pseudo,
            ax=ax,
            lumi=args.lumi,
            lumi_format="{:0.0f}",
            com=args.com,
            supp=args.pub,
            year=args.year,
        )
        # ax.semilogy()
        # ax.set_ylim(10, None)

        # Sci notat
        leading_dig_max, decimal_dig_max = 0, 0
        for tick in ax.get_yticks():
            leading_dig_max = max(leading_dig_max, get_digits(tick)[0])
            decimal_dig_max = max(decimal_dig_max, get_digits(tick)[1])
        if (leading_dig_max > 3) or (decimal_dig_max > 3):

            def g(x, pos):
                return rf"${sci_notation(x, sig_fig=1, no_zero=args.no_zero)}$"

            ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(g))

        # Save
        for fmt in format_list:
            out_path = out_dir / task.fittype / f"{task.savename}_{task.fittype}.{fmt}"
            logging.debug(f"Saving: '{out_path}'")
            fig.savefig(
                out_path,
                format=fmt,
                dpi=args.dpi,
                bbox_inches="tight",
                # transparent=True,
            )
    finally:
        if semaphore is not None:
            semaphore.release()


def main():
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
        help="Output folder (will becreated if it doesn't exist).",
    )
    parser.add_argument(
        "--fit",
        default="all",
        choices=["all", "prefit", "fit_s", "fit_b"],
        dest="fit",
        help="Shape set to plot.",
    )
    parser.add_argument(
        "--cats",
        default=None,
        dest="cats",
        help="Categories to plot. Either a comma-separated list of categories to plot (`cat1,cat2`) or a mapping of categories to plot and/or merge (`mcat1:cat1,cat2;mcat2:cat3,cat4`).",
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
        "-p",
        nargs="?",
        default=0,
        const=10,
        type=int,
        dest="multiprocessing",
        help="Use multiprocessing. May fail due to parallel reads from fitDiag. `-p` defaults to 10 processes.",
    )
    parser_data = parser.add_argument_group(
        "Data",
        description="What type of data is stored in 'data_obs' in the input file.",
    )
    pseudo = parser_data.add_mutually_exclusive_group(required=True)
    pseudo.add_argument("--data", action="store_false", dest="pseudo")
    pseudo.add_argument("--MC", action="store_true", dest="pseudo")
    pseudo.add_argument("--toys", action="store_true", dest="toys")
    parser_data.add_argument(
        "--unblind",
        action="store_true",
        dest="unblind",
        help="Confirm wanting to plot real data",
    )
    parser_data.add_argument(
        "--blind",
        type=str,
        default=None,
        help="Category to blind data (not plotted), e.g. `cat1`",
    )
    parser_data.add_argument(
        "--blind-data",
        "--blind_data",
        dest="blind_data",
        type=str,
        default=None,
        help="Range of data to blind in a category, e.g. `cat1:3:6` (bins 3-5 by index), `cat2:3j:6j` (bins with edges 3-6 by value). Multiple categories: `cat1:1:5;cat2:2:4`",
    )
    parser_plot = parser.add_argument_group("Stacking options")
    parser_plot.add_argument(
        "--sigs",
        default=None,
        dest="sigs",
        help="Signals. Comma-separated list of keys available in provided --style sty.yml file, e.g. `ggH,VBF`",
    )
    parser_plot.add_argument(
        "--project-signals",
        "--project_signals",
        default=None,
        dest="project_signals",
        help="Project signals onto the x-axis at scale. Comma-separated list of values of equal length with --sigs, e.g. `1,1`.",
    )
    parser_plot.add_argument(
        "--bkgs",
        default=None,
        dest="bkgs",
        help="Backgrounds. Comma-separated list of keys available in provided `--style sty.yml` file, e.g. `qcd,ttbar`",
    )
    parser_plot.add_argument(
        "--onto",
        default=None,
        dest="onto",
        help="Background to plot unfilled and stack other processes onto, e.g. `qcd`. Useful when one background is dominant.",
    )
    parser_plot.add_argument(
        "--rmap",
        default=None,
        dest="rmap",
        # type=json.loads,
        help="A dict-like string (`hbb:r_q,htt:r_t`) mapping signal keys in --sigs to POIs in --input fitDiagnostics file (requires ROOT).",
    )
    parser_styling = parser.add_argument_group("Styling")
    parser_styling.add_argument(
        "--style",
        "-s",
        default=None,
        dest="style",
        help="Style yaml file e.g. `style.yml`. Automatically created as `sty.yml` if not provided.",
    )
    parser_styling.add_argument(
        "--cmap",
        type=str,
        default=None,
        help="Name of `cmap` to fill colors in `sty.yml` from. Eg.: Tiepolo;Renoir;tab10. Only used if `sty.yml` is not provided.",
    )
    parser_styling.add_argument(
        "--cmslabel",
        default="Private Work",
        type=str,
        help="CMS Label.",
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
        "--lumi",
        default=None,
        type=float,
        help="Luminosity for label.",
    )
    parser_styling.add_argument(
        "--xlabel",
        default=None,
        type=str,
        help="Plot x-label eg `$m_{\\tau\\bar{\\tau}}^{reg}$`. "
        "If left `None` will read from combine. When using latex enclose string as 'str'.",
        #  If copying the above sequence from code use `$m_{\tau\bar{\tau}}^{reg}$`
    )
    parser_styling.add_argument(
        "--ylabel",
        default=None,
        type=str,
        help="Plot y-label. If left `None` will read from combine. When using latex enclose string as 'str'.",
    )
    parser_styling.add_argument(
        "--catlabels",
        default=None,
        type=str,
        help="Category label to replace automated labelling. To pass per-category label, use `;` separator.",
    )
    parser_styling.add_argument(
        "--clipx",
        type=str2bool,
        const=True,
        nargs="?",
        default=True,
        choices=[True, False],
        help="Clip x-axis to range of data.",
    )
    parser_styling.add_argument(
        "--no_zero",
        type=str2bool,
        const=True,
        nargs="?",
        default=False,
        choices=[True, False],
        help="Hide zeroth tick on the y-axis.",
    )
    parser_styling.add_argument(
        "--dpi",
        default=300,
        type=int,
        help="DPI for png format.",
    )
    parser_debug = parser.add_argument_group("DEBUG Options")
    parser_debug.add_argument("--verbose", "-v", "-_v", action="store_true", help="Verbose logging")
    parser_debug.add_argument("--debug", "-vv", "--vv", action="store_true", help="Debug logging")
    parser_debug.add_argument(
        "--chi2",
        dest="chi2",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
        choices=[True, False],
        help="Display chi2 (when plotting multiple categories a per-category sum is displayed).",
    )
    parser_debug.add_argument(
        "--chi2_nocorr",
        dest="chi2_nocorr",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
        choices=[True, False],
        help="Use naive chi2 instead (no covariance matrix).",
    )
    parser_debug.add_argument(
        "--residuals",
        dest="residuals",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
        choices=[True, False],
        help="Display data/MC residuals.",
    )
    parser_debug.add_argument("--noroot", action="store_true", help="Skip ROOT dependency")

    import textwrap

    epilog = textwrap.dedent(
        """
    Minimal example:
    ```
    combine_postfits -i fitDiagnosticsTest.root --toys
    ```

    Basic usage (modify generated `sty.yml` file) with debug options on:
    ```
    combine_postfits -i fitDiagnosticsTest.root --sigs hbb --bkgs qcd,wjets,zjets,ttbar --rmap 'hbb:r' --onto qcd --style sty.yml
    --data --unblind
    --cmslabel 'Private Work' --year 2016 --lumi 35.9 --xlabel '$m_{b\\bar{b}}^{reg}$'
    --chi2 True --residuals True -p
    ```

    Extended example with category merging and signal mapping
    ```
    combine_postfits -i fitDiagnosticsTest.root -o final_plots --style sty.yml
    --data --unblind --sigs hbb,zbb --bkgs top,ttbat,wjets,wcq,zjets_other --onto qcd
    --rmap zbb:r_z,hbb:r  --project-signal 50,0
    --cats 'pass16:ptbin*pass2016;pass:ptbin*pass*;fail:ptbin*fail*;muCRpass16:muonCRpass2016'
    -p 20
    ```

    For more examples see https://github.com/andrzejnovak/combine_postfits/blob/master/tests/test.sh
    """
    )
    parser_epi = parser.add_argument_group("Examples:", description=epilog)

    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Arg processing
    utils.setup_logging(verbose=args.verbose, debug=args.debug)
    if not args.pseudo and not args.unblind and args.blind is None and args.blind_data is None:
        unblind_conf = Confirm.ask(
            "Option `--blind` or `--blind-data` is not set, while plotting with `--data`. "
            "Hi Eric, are you sure you want to unblind? (pass `--unblind` to suppress this prompt)"
        )
        assert unblind_conf, "Unblind option not confirmed. Exiting."

    if args.fit == "all":
        fit_types = ["prefit", "fit_s"]
    else:
        fit_types = [args.fit]
    for fit in fit_types:
        (out_dir / fit).mkdir(parents=True, exist_ok=True)
    if args.format == "both":
        format = ["png", "pdf"]
    else:
        format = [args.format]

    # Make plots

    fd = uproot.open(args.input)
    if ROOT_AVAILABLE and not args.noroot:
        rfd = r.TFile.Open(args.input)
    else:
        rfd = None

    try:
        if args.style is not None:
            with open(args.style, "r") as stream:
                style = yaml.safe_load(stream)
        else:
            style = utils.make_style_dict_yaml(fd, cmap=args.cmap, sort=True, sort_peaky=True)
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

        # Parse rmap (signal-to-POI mapping); blinding is resolved inside generate_plot_tasks()
        rmap = None
        if args.rmap is not None:
            rmap = {}
            for kv in args.rmap.split(","):
                if ":" not in kv:
                    logging.error(f"Invalid rmap entry '{kv}', expected 'key:value'. Skipping.")
                    continue
                key, val = kv.split(":", 1)
                rmap[key] = val
            logging.debug(f"Signal-to-POI mapping:\n{rmap}")

        # Warn about any signals that lack an rmap entry (also catches partial --rmap)
        if args.sigs:
            _unset_sigs = [sig for sig in args.sigs.split(",") if rmap is None or sig not in rmap]
            if _unset_sigs:
                logging.warning(
                    f"Signals '{','.join(_unset_sigs)}' not found in rmap: `{rmap}`. To display signal strengths pass `--rmap '{','.join([f'{_sig}:r_param' for _sig in _unset_sigs])}'`."
                )

        # Generate Tasks
        # We iterate over tasks yielded by the generator
        _procs: list[Process] = []
        n_tasks = 0
        all_tasks = []  # Store tasks to allow for label parsing and progress bar total
        for task in generate_plot_tasks(args, fit_types, fd):
            n_tasks += 1
            all_tasks.append(task)
            logging.debug(f"Processing task: {task}")

        if n_tasks == 0:
            logging.warning("No plotting tasks generated. Check your --cats or --fit options.")
            sys.exit(0)

        # Label parsing for list mode (legacy support for semicolon-separated labels matching task order)
        # This is a bit fragile but maintains backward compatibility if user passed a list of labels
        if args.catlabels is not None and ";" in args.catlabels and args.cats and ":" not in args.cats:
            labels_list = args.catlabels.split(";")
            if len(labels_list) == len(all_tasks):
                for i, task in enumerate(all_tasks):
                    task.label = labels_list[i]
            else:
                logging.warning(
                    f"Number of labels ({len(labels_list)}) does not match number of plots ({len(all_tasks)}). Ignoring labels."
                )

        # Check for overlaps
        from collections import defaultdict

        channel_to_cats = defaultdict(list)
        for task in all_tasks:
            for channel in task.channels:
                channel_to_cats[(task.fittype, channel)].append(task.savename)

        overlaps = {k: cats for k, cats in channel_to_cats.items() if len(cats) > 1}
        if overlaps:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            summary_table = Table(
                title="[bold red]Overlapping Categories Detected[/bold red]",
                show_header=True,
                header_style="bold magenta",
                show_lines=True,
            )
            summary_table.add_column("Fit Type", style="cyan")
            summary_table.add_column("Category", style="green")
            summary_table.add_column("Total", justify="right")
            summary_table.add_column("Composition (Red = Overlap)")

            for task in all_tasks:
                n_channels = len(task.channels)

                task_has_overlap = any((task.fittype, ch) in overlaps for ch in task.channels)
                if not task_has_overlap:
                    continue

                formatted_channels = [
                    f"[bold red]{ch}[/bold red]" if (task.fittype, ch) in overlaps else ch for ch in task.channels
                ]
                composition_str = ", ".join(formatted_channels)
                summary_table.add_row(task.fittype, task.savename, str(n_channels), composition_str)

            console.print(summary_table)

            if not Confirm.ask("[bold red]Do you want to continue with double-counted channels?[/bold red]"):
                sys.exit("Aborted by user due to overlapping categories.")

        # Process Tasks
        _procs = []
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            SpinnerColumn(),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
        ) as progress:
            prog_str_fmt = "[red]Plotting ({} workers): " if args.multiprocessing > 0 else "[red]Plotting: "
            prog_str = prog_str_fmt.format("N")
            prog_plotting = progress.add_task(prog_str, total=len(all_tasks))
            semaphore = Semaphore(args.multiprocessing)

            for task in all_tasks:
                # Resolve label if still None
                if task.label is None:
                    # Default label logic: use savename, replace \n
                    task.label = task.savename

                # Format label for plotting (translate literal '\n' into real newlines)
                task.label = "\n".join(str(task.label).split(r"\n"))

                if args.multiprocessing > 0:
                    semaphore.acquire()
                    p = Process(
                        target=process_plot,
                        args=(
                            semaphore,
                            fd,
                            rfd,
                            task,
                            style,
                            rmap,
                            args,
                            out_dir,
                            format,
                        ),
                        name=task.savename,
                    )
                    _procs.append(p)
                    p.start()
                    time.sleep(0.1)

                    n_running = sum([p.is_alive() for p in _procs])
                    progress.update(
                        prog_plotting,
                        completed=len(_procs) - n_running,
                        refresh=True,
                        description=prog_str_fmt.format(n_running),
                    )
                    time_check(progress, _procs, 6)
                else:
                    process_plot(
                        None,
                        fd,
                        rfd,
                        task,
                        style,
                        rmap,
                        args,
                        out_dir,
                        format,
                    )
                    progress.update(prog_plotting, advance=1, refresh=True)
            if args.multiprocessing > 0:
                while sum([p.is_alive() for p in _procs]) > 0:
                    n_running = sum([p.is_alive() for p in _procs])
                    progress.update(
                        prog_plotting,
                        completed=len(_procs) - n_running,
                        refresh=True,
                        description=prog_str_fmt.format(n_running),
                    )
                    time.sleep(0.1)

                    time_check(progress, _procs, 6)
            progress.update(
                prog_plotting,
                completed=n_tasks,
                total=n_tasks,
                refresh=True,
                description=prog_str_fmt.format(0),
            )

    finally:
        fd.close()
        if rfd:
            rfd.Close()


if __name__ == "__main__":
    main()
