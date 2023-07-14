import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import mplhep as mplhep
plt.style.use(mplhep.style.ATLAS)
plt.rcParams['axes.linewidth'] = 3

def create_fig_with_n_panels(ncols, nrows, h_ratio = None):
    # now we make a figure
    fig    = plt.figure(figsize=(24, 18))

    if h_ratio is None: height_ratios = [3,*[1]*(nrows-1)]
    else:  height_ratios = h_ratio
    gs     = fig.add_gridspec(ncols=ncols, nrows=nrows, height_ratios=height_ratios, hspace=0.1)
    ax     = fig.add_subplot(gs[0, 0])
    rat_axes = []
    for i in range(nrows-1):
        rat_ax = fig.add_subplot(gs[i+1, 0], sharex=ax)
        rat_axes.append(rat_ax)

    plt.rcParams.update({'font.size': 20})
    return fig, ax, rat_axes

def plot_stack(stackables, data, axis, blind=None, title=''):

    stackables = sorted(stackables, key=lambda x: x.h.values().sum(), reverse=True)
    histos = [stackable.h for stackable in stackables]
    colors = [stackable.sample.color for stackable in stackables]
    labels = [stackable.sample.label  for stackable in stackables]
    data_h = data.h
    mplhep.histplot(histos, color = colors, label = labels, ax = axis, histtype='fill', stack=True, zorder=1)
    axis.scatter(data_h.axes.centers[0][~blind], data_h.values()[~blind], color = 'black', marker='x', s=70, zorder=2, label='Data')

    if blind is not None:
        rect = None
        for bin_idx, bin_is_blinded in enumerate(blind):
            if bin_is_blinded:
                shade_x1, shade_x2 = data_h.axes.edges[0][bin_idx:bin_idx+2] # Last index is not inclusive

                # Draw Rectangle
                axis.axvspan(shade_x1, shade_x2, facecolor='blue', alpha=0.06, lw=0, zorder = 3)
                # Draw Hatch
                axis.axvspan(shade_x1, shade_x2, facecolor='none', edgecolor='grey', hatch="//", alpha=0.5, lw=1., zorder = 4, label = 'Blinded')


    axis.legend(bbox_to_anchor=(1.04, 1), loc="upper left", ncol=2)
    axis.set_ylabel("Number of Events")


    if any(any(h.values()>0) for h in histos) :
        axis.set_yscale("log")

    plt.setp(axis.get_xticklabels(), visible=False)

    # X-label
    axis.set_xlabel('')

    #Title
    axis.set_title(title, pad=25)


def plot_datamc(mc, data, blind, xlabel, axis):

    data_vals = data.values()
    data_vars = data.variances()
    mc_vals   = mc.values()
    mc_vars   = mc.variances()

    # Data Points

    ratio = np.divide(data_vals, mc_vals, out = np.full_like(data_vals,0), where = (mc_vals > 0) & (~blind))
    err1  = np.sqrt(data_vars, out = np.full_like(data_vals, 0), where = data_vars >=0)
    err2  = mc_vals
    err   = np.divide(err1, err2, out = np.full_like(data_vals,1e3), where = err2 > 0)

    axis.errorbar(data.axes.centers[0], ratio, err, color = 'black', marker = 'x', linestyle='None', label = None)

    # MC Uncertainty band
    rel_mc_stat_1 = np.sqrt(mc_vars, out = np.full_like(mc_vals, 0), where = mc_vars >=0)
    rel_mc_stat_2 = mc_vals
    rel_mc_stat = np.divide(rel_mc_stat_1, rel_mc_stat_2, out = np.full_like(mc_vals, 1e3), where = rel_mc_stat_2 > 0)

    bin_edges = mc.axes.edges[0]
    bin_width = (bin_edges[1:] - bin_edges[:-1])

    nom_unct = axis.bar(mc.axes.centers[0],
                        2 * rel_mc_stat,
                        width= bin_width,
                        bottom=1.0 - rel_mc_stat,
                        fill=False,
                        linewidth=0,
                        edgecolor="gray",
                        hatch=3 * "/",
                        )

    # panel ylimits

    axis.set_ylim((0.8,1.2))
    axis.set_xlabel(xlabel, fontsize=24)
    axis.grid(True)

    return nom_unct

def plot_separation(signal_histo, bkg_histos, axis, signal_color, signal_name):

    signal = signal_histo.h
    bkg    = sum(bkg_histo.h for bkg_histo in bkg_histos)

    signal_copy = signal.copy()
    bkg_copy    = bkg.copy()

    signal_vals = signal_copy.values(flow=True)
    bkg_vals    = bkg_copy.values(flow=True)

    signal_copy *= 1/sum(signal_vals) if sum(signal_vals) > 0 else 0
    bkg_copy    *= 1/sum(bkg_vals)    if sum(bkg_vals)    > 0 else 0

    mplhep.histplot([signal_copy, bkg_copy], color = [signal_color, 'black'], label = [signal_name, 'Total Background'], ax = axis)

    axis.legend(ncol=1, loc='best')
    axis.set_ylabel("a.u. (Normalised)")


def plot_signif_per_bin(signal_histo, signif, err, axis, last_ax):

    signal_h = signal_histo.h

    binedges   = signal_h.axes.edges[0]
    binwidths  = binedges[1:] - binedges[:-1]
    bincenters = signal_h.axes.centers[0]

    axis.bar( bincenters, signif, width = binwidths,   color = signal_histo.sample.color, align='center', joinstyle='round', alpha=0.8)
    axis.errorbar(bincenters, signif, err, alpha=0.4, color = 'black', linestyle = 'None')

    # Signficance panel y-label
    axis.set_ylabel(f"{signal_histo.sample.name}"+r"$/\sqrt{B}$", rotation=0, fontsize=20, labelpad=50, verticalalignment='center', loc='center')

    # Signficance panel ylimits
    max_signif = signif.max()
    min_signif = signif.min()
    if min_signif == max_signif == 0:
        min_signif = 0
        max_signif = 1

    axis.set_ylim((min_signif*1.5, max_signif*1.5))
    axis.grid(True)

    if not last_ax:
        plt.setp(axis.get_xticklabels(), visible=False)
    else:
        axis.set_xlabel(signal_histo.label, fontsize=24)