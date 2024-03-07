import os
import ROOT as r
import uproot
import logging
import yaml
import matplotlib
matplotlib.use('Agg')
import mplhep as hep
import matplotlib.pyplot as plt
import argparse

from plot import plot
hep.style.use("CMS")



if __name__ == '__main__':
    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')


    parser = argparse.ArgumentParser()
    parser.add_argument("-i",
                        "--input",
                        default='fitDiagnosticsTest.root',
                        help="Input shapes file")
    parser.add_argument("--fit",
                        default="all",
                        choices={"prefit", "fit_s", "all"},
                        dest='fit',
                        help="Shapes to plot")
    parser.add_argument("-o",
                        "--output-folder",
                        default='plots',
                        dest='output_folder',
                        help="Folder to store plots - will be created if it doesn't exist.")
    parser.add_argument("--year",
                        default=None,
                        choices={"2016", "2017", "2018", ""},
                        type=str,
                        help="year label")
    parser.add_argument('-f',
                        "--format",
                        type=str,
                        default='both',
                        choices={'png', 'pdf', 'both'},
                        help="Plot format")

    pseudo = parser.add_mutually_exclusive_group(required=True)
    pseudo.add_argument('--data', action='store_false', dest='pseudo')
    pseudo.add_argument('--MC', action='store_true', dest='pseudo')
    pseudo.add_argument('--toys', action='store_true', dest='toys')

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--debug", "-vv", action="store_true", help="Debug logging")
    args = parser.parse_args()
    
    os.makedirs(args.output_folder, exist_ok=True)
    
    # Arg processing
    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)
    
    if args.fit == 'all':
        fit_types = ['prefit', 'fit_s']
    else:
        fit_types = [args.fit]
    if args.format == 'both':
        format = ['png', 'pdf']
    else:
        format = [args.format]

    # Make plots
    fd = uproot.open(args.input)
    rfd = r.TFile.Open(args.input)
    with open("style_eric.yml", "r") as stream:
        try:
            style = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    for fit_type in fit_types:
        channels = [c[:-2] for c in fd[f"shapes_{fit_type}"].keys() if c.count("/") == 0]
        for channel in channels:

            fig, (ax, rax) = plot(fd, fit_type, cats=[channel], restoreNorm=True,
                sigs = ['phitt125'],
                bkgs = ['multijet', 'top', 'wlnu', "dy", "htt125"],
                clipx=True,
                fitDiag_root=rfd,
                style=style,
                cat_info=1,
            )
            rax.set_xlabel(r"$m_{\tau\bar{\tau}}^{reg}$")
            hep.cms.label("Private Work", data=False, ax=ax)
            for fmt in format:
                fig.savefig(f"{args.output_folder}/{channel}_{fit_type}.{fmt}", format=fmt)
