# Installation

```
gh repo clone andrzejnovak/combine_postfits
cd combine_postfits
pip install -e .
```

# Run

Default plotter can be ran as `combine_postfits -i fitDiagnostics.root`. If you
need further customization edit the source file at `make_plot.py`, which can be
also copied separately and edited as needed.


```bash
USAGE: combine_postfits [-h] [--input INPUT] [--output OUTPUT] [--fit {all,prefit,fit_s,fit_b}] [--cats CATS] [--format {png,pdf,both}] [-p [MULTIPROCESSING]]
                        (--data | --MC | --toys) [--unblind] [--blind BLIND] [--sigs SIGS] [--project-signals PROJECT_SIGNALS] [--bkgs BKGS] [--onto ONTO] [--rmap RMAP]
                        [--style STYLE] [--cmap CMAP] [--cmslabel CMSLABEL] [--year {2016,2017,2018,""}] [--pub PUB] [--lumi LUMI] [--xlabel XLABEL] [--ylabel YLABEL]
                        [--catlabels CATLABELS] [--clipx [{True,False}]] [--no_zero [{True,False}]] [--dpi DPI] [--verbose] [--debug] [--chi2 [{True,False}]]
                        [--residuals [{True,False}]] [--noroot]

OPTIONS:
  -h, --help            show this help message and exit
  --input, -i INPUT     Input combine fitDiagnostics file (default: fitDiagnosticsTest.root)
  --output, -o OUTPUT   Output folder (will becreated if it doesn\'t exist). (default: plots)
  --fit {all,prefit,fit_s,fit_b}
                        Shape set to plot. (default: all)
  --cats CATS           Categories to plot. Either a comma-separated list of categories to plot (`cat1,cat2`) or a mapping of categories to plot and/or merge
                        (`mcat1:cat1,cat2;mcat2:cat3,cat4`).
  --format, -f {png,pdf,both}
                        Plot output format (default: png)
  -p [MULTIPROCESSING]  Use multiprocessing. May fail due to parallel reads from fitDiag. `-p` defaults to 10 processes.

DATA:
  What type of data is stored in 'data_obs' in the input file.

  --data
  --MC
  --toys
  --unblind             Confirm wanting to plot real data
  --blind BLIND         Category to blind data (not plotted), e.g. `cat1`

STACKING OPTIONS:
  --sigs SIGS           Signals. Comma-separated list of keys available in provided --style sty.yml file, e.g. `ggH,VBF`
  --project-signals, --project_signals PROJECT_SIGNALS
                        Project signals onto the x-axis at scale. Comma-separated list of values of equal length with --sigs, e.g. `1,1`.
  --bkgs BKGS           Backgrounds. Comma-separated list of keys available in provided `--style sty.yml` file, e.g. `qcd,ttbar`
  --onto ONTO           Background to plot unfilled and stack other processes onto, e.g. `qcd`. Useful when one background is dominant.
  --rmap RMAP           A dict-like string (`hbb:r_q,htt:r_t`) mapping signal keys in --sigs to POIs in --input fitDiagnostics file (requires ROOT).

STYLING:
  --style, -s STYLE     Style yaml file e.g. `style.yml`. Automatically created as `sty.yml` if not provided.
  --cmap CMAP           Name of `cmap` to fill colors in `sty.yml` from. Eg.: Tiepolo;Renoir;tab10. Only used if `sty.yml` is not provided.
  --cmslabel CMSLABEL   CMS Label. (default: Private Work)
  --year {2016,2017,2018,""}
                        Year label.
  --pub PUB             Supplementary label - arxiv no.
  --lumi LUMI           Luminosity for label.
  --xlabel XLABEL       Plot x-label eg `$m_{\tau\bar{\tau}}^{reg}$`. If left `None` will read from combine. When using latex enclose string as 'str'.
  --ylabel YLABEL       Plot y-label. If left `None` will read from combine. When using latex enclose string as 'str'.
  --catlabels CATLABELS
                        Category label to replace automated labelling. To pass per-category label, use `;` separator.
  --clipx [{True,False}]
                        Clip x-axis to range of data. (default: True)
  --no_zero [{True,False}]
                        Hide zeroth tick on the y-axis.
  --dpi DPI             DPI for png format. (default: 300)

DEBUG OPTIONS:
  --verbose, -v, -_v    Verbose logging
  --debug, -vv, --vv    Debug logging
  --chi2 [{True,False}]
                        Display chi2 (when plotting multiple categories a per-category sum is displayed).
  --residuals [{True,False}]
                        Display data/MC residuals.
  --noroot              Skip ROOT dependency

EXAMPLES::

  Minimal example:
  ``
  combine_postfits -i fitDiagnosticsTest.root --toys
  ``

  Basic usage (modify generated `sty.yml` file) with debug options on:
  ``
  combine_postfits -i fitDiagnosticsTest.root --sigs hbb --bkgs qcd,wjets,zjets,ttbar --rmap 'hbb:r' --onto qcd --style sty.yml
  --data --unblind
  --cmslabel 'Private Work' --year 2016 --lumi 35.9 --xlabel '$m_{b\bar{b}}^{reg}$'
  --chi2 True --residuals True -p
  ``

  Extended example with category merging and signal mapping
  ``
  combine_postfits -i fitDiagnosticsTest.root -o final_plots --style sty.yml
  --data --unblind --sigs hbb,zbb --bkgs top,ttbat,wjets,wcq,zjets_other --onto qcd
  --rmap zbb:r_z,hbb:r  --project-signal 50,0
  --cats 'pass16:ptbin*pass2016;pass:ptbin*pass*;fail:ptbin*fail*;muCRpass16:muonCRpass2016'
  -p 20
  ``

  For more examples see https://github.com/andrzejnovak/combine_postfits/blob/master/tests/test.sh

  ```
```



# Examples

In `cd test` directory:


- `fit_diag_A.root`
  - Simple
  ```bash
  combine_postfits -i fitDiags/fit_diag_A.root -o outs/plots_A_all --data --unblind  -p
  ```

  - Customized
  ```bash
  combine_postfits -i fitDiags/fit_diag_A.root -o outs/plots_A --style styles/style_A.yml --data --unblind --sigs hcc,zcc --onto qcd --rmap zcc:z,hcc:r  --cats 'pass:ptbin*pass2016;fail:ptbin*fail*;muCRpass:muonCRpass2016;muCRfail:muonCRfail2016' --bkgs top,other,wqq,wcq,zqq,zbb,hbb -vv --project-signal 200,0 -p
  ```

- `fit_diag_Abig.root`
  - Simple
  ```bash
  combine_postfits -i fitDiags/fit_diag_Abig.root -o outs/plots_Abig_all --data --unblind  -p
  ```

  - Customized
  ```bash
  combine_postfits -i fitDiags/fit_diag_Abig.root -o outs/plots_Abig --style styles/style_A.yml --data --unblind --sigs hcc,zcc --onto qcd --rmap zcc:z,hcc:r  --cats 'pass16:ptbin*pass2016;fail16:ptbin*fail2016;pass17:ptbin*pass2017;fail17:ptbin*fail2017;pass18:ptbin*pass2018;fail18:ptbin*fail2018;pass:ptbin*pass*;fail:ptbin*fail*;muCRpass16:muonCRpass2016;muCRfail16:muonCRfail2016;muCRpass17:muonCRpass2017;muCRfail17:muonCRfail2017;muCRpass18:muonCRpass2018;muCRfail18:muonCRfail2018' --bkgs top,other,wqq,wcq,zqq,zbb,hbb -vv --project-signal 200,0 -p
  ```

- `fit_diag_B.root`
  - Simple
  ```bash
  combine_postfits -i fitDiags/fit_diag_B.root -o outs/plots_B_all --MC  -p
  ```

  - Customized
  ```bash
  combine_postfits -i fitDiags/fit_diag_B.root --data --unblind -o outs/plots_B --style styles/style_B.yml  --xlabel 'Jet $m_{SD}$' --sigs b150,m150 --project-signals 2,2 --rmap 'm150:r_q,b150:r_b' --bkgs top,vlep,wqq,zqq,zbb,hbb --onto 2017_qcd --cats 'fail:ptbin*fail;passlow:ptbin*high*;passhigh:ptbin*passlow*' -v -p

  # 'mufail:muonCRfail;mupasslow:muonCRpasslowbvl;mupasshigh:muonCRpasshighbvl'
  ```



- `fit_diag_C.root`
  - Simple
  ```bash
  combine_postfits -i fitDiags/fit_diag_C.root -o outs/plots_C_all --toys  -p
  ```

  - Customized
  ```bash
  combine_postfits -i fitDiags/fit_diag_C.root -o outs/plots_C --toys  --style styles/style_C.yml --xlabel 'Jet $m_{reg}$'
  ```
  
- `fit_diag_D.root`
  - Simple
  ```bash
  combine_postfits -i fitDiags/fit_diag_D.root -o outs/plots_D_all --MC  -p
  ```

  - Customized
  ```bash
  combine_postfits -i fitDiags/fit_diag_D.root -o outs/plots_D --MC --style styles/style_D.yml --onto qcd --sigs VH --bkgs qcd,top,Wjets,Zjets,VV,H  --rmap 'VH:rVH' --project-signals 3 --xlabel 'Jet $m_{SD}$' -p 20
  ```
