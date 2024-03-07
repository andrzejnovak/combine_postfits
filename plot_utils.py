import logging
# import warnings
# import yaml
import uproot
# import mplhep as hep
# logging.getLogger('matplotlib').setLevel(logging.WARN)
import matplotlib.pyplot as plt
import numpy as np
# import pprint
# # set up pretty printer
# pp = pprint.PrettyPrinter(indent=2, sort_dicts=False)
# def log_pretty(obj):
#     pretty_out = f"{pp.pformat(obj)}"

#     return f'{pretty_out}\n'
import hist
from cycler import cycler
# np.seterr(divide='ignore', invalid='ignore')

# Only have to do this to read fit results :/
# import ROOT as r

def clean_yaml(style):
    for key in style:
        # Clean keys
        for elem in style[key]:
            if elem not in ['label', 'color', 'hatch', 'contains']:
                logging.warning(f"Unexpected key: '{elem}' for sample: '{key}'. Allowed keys are: 'label', 'color', 'hatch', 'contains'.")
        # Standardize keys:
        for elem in ['label', 'color', 'hatch']:
            if elem not in style[key]:
                style[key][elem] = None
        # Clean raw-strings (for latex in mpl)
        if style[key]['label'].startswith("r"):
            style[key]['label'] = style[key]['label'].split('"')[1]
        # Clean Nones:
        for elem in style[key]:
            if isinstance(style[key][elem], str) and style[key][elem].lower() == 'none':
                style[key][elem] = None
        # Parse `contains` to a list
        if 'contains' in style[key] and style[key]['contains'] is not None and not isinstance(style[key]['contains'], list):
            style[key]['contains'] = style[key]['contains'].split()
    return style

def extract_mergemap(style):
    compound_keys = [key for key in style if 'contains' in style[key] and style[key]['contains'] is not None]
    return {key: style[key]['contains'] for key in compound_keys}

def fill_colors(style, cmap=None, no_duplicates=True):
    if cmap is None:
        cmap = plt.rcParams['axes.prop_cycle'].by_key()['color']
    taken = [style[key]['color'] for key in style if 'color' in style[key] and style[key]['color'] is not None]
    cmap_clean = cmap.copy()
    if no_duplicates:
        for c in taken:
            if c in cmap_clean:
                cmap_clean.remove(c)
    if len(cmap_clean) == 0: 
        logging.error(f"len(cmap) after cleaning is 0. Either pass longer 'cmap' or set `no_duplicates=False`." )
        cmap_clean = cmap
    cycler_iter = cycler("color", cmap_clean)()
    counter = 0
    for key in style:
        if 'color' not in style[key] or style[key]['color'] is None:
            pop_col = next(cycler_iter)
            counter +=1
            logging.info(f"Key 'color' not found for sample '{key}'. Setting to: '{pop_col}'", )
            style[key]['color'] = pop_col['color']
    if counter > len(cmap):
        logging.warning(f"'cmap' is too short. There will be {counter-len(cmap)} duplicate colors.", )
    for key, color, label in zip(['data', 'total_signal'], ['k', 'red'], ['Data', 'Signal']):
        if key not in style:
            logging.warning(f"Sample: '{key}' is not present in style_dict. It will be created with default values.")
            style[key] = {'color': color, 'label': label}
    return style

cmap6 = ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"]
cmap10 = ["#3f90da", "#ffa90e", "#bd1f01", "#94a4a2", "#832db6", "#a96b59", "#e76300", "#b9ac70", "#717581", "#92dadd"]

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
    leg1 = ax.legend(handles=handles[:split],
                     labels=labels[:split],
                     ncol=ncols,
                     loc="upper right",
                     **kw)
    if nentries % 2 == 0:
        return leg1

    ax.add_artist(leg1)
    leg2 = ax.legend(handles=handles[split:],
                     labels=labels[split:],
                     ncol=nentries - nentries // ncols * ncols,
                     **kw)

    leg2.remove()

    leg1._legend_box._children.append(leg2._legend_handle_box)
    leg1._legend_box.stale = True
    return leg1

def format_categories(cats, n=2):
    # cat, cat \n cat, cat
    lab_cats = np.array(["x"]*(2*len(cats)-1), dtype='object')
    lab_cats[0::2] = cats
    lab_cats[1::2][n-1::n] = '\n'
    for i in range(len(lab_cats)):
        if lab_cats[i] == "x":
            lab_cats[i] = ","
    return "".join(list(lab_cats))

# fitDiag extraction
def get_fit_val(fitDiag, val, fittype='fit_s', substitute=1.):
    if fitDiag is None:
        return substitute
    if val in fitDiag.Get(fittype).floatParsFinal().contentsString().split(','):
        return fitDiag.Get(fittype).floatParsFinal().find(val).getVal()
    else:
        return substitute
    
def get_fit_unc(fitDiag, val, fittype='fit_s', substitute=(0,0)):
    if fitDiag is None:
        return substitute
    if val in fitDiag.Get(fittype).floatParsFinal().contentsString().split(','):
        rval = fitDiag.Get(fittype).floatParsFinal().find(val)
        return (abs(rval.getAsymErrorLo()), rval.getAsymErrorHi())
    else:
        return substitute
    
    
# Object conversion
def tgasym_to_err(tgasym, restoreNorm=True):
    x, y = tgasym.values("x"), tgasym.values("y")
    xlo, xhi = tgasym.errors("low", axis="x"), tgasym.errors("high", axis="x")
    ylo, yhi = tgasym.errors("low", axis="y"), tgasym.errors("high", axis="y")
    bins = np.r_[(x - xlo), (x+xhi)[-1]]
    binwidth = xlo+xhi
    if restoreNorm:
        y = y * binwidth
        ylo = ylo * binwidth
        yhi = yhi * binwidth
    return y, bins, ylo, yhi

def tgasym_to_hist(tgasym, restoreNorm=True):
    y, bins, ylo, yhi = tgasym_to_err(tgasym, restoreNorm)
    h = hist.new.Var(bins).Weight()
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
    return sum([geth(name, shapes_dir, restoreNorm=restoreNorm) for shapes_dir in channels])

def geths(names, channels, sort=True, restoreNorm=True):
    if sort:
        sorted_names = [k for k, v in style_set_A['label_dict'].items() if k in names]
        assert len(sorted_names) == len(names), f"Sorting incomplete: {names} -> {sorted_names}"
        names = sorted_names
    if isinstance(channels, list):  # channels = [shapes_dir, shapes_dir]
        return {name: getha(name, channels, restoreNorm=restoreNorm) for name in names}
    else:  # channels = shapes_dir
        return {name: geth(name, channels, restoreNorm=restoreNorm) for name in names}

def merge_hists(hist_dict, merge_map):
    for k, v in merge_map.items():
        if k in hist_dict and k != v[0]:
            logging.warning(f"Won't add merge `{k} : {v}` because histogram: `{k}` already exists.")
            continue
        to_merge = []
        for name in v:
            if name not in hist_dict:
                logging.warning(f"Histogram `{name}` is not available in channel for a merge {v} -> {k}.")
            else:
                to_merge.append(hist_dict[name])
        hist_dict[k] = sum(to_merge) 
    return hist_dict

