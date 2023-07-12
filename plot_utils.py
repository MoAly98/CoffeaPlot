import mplhep as hep
import matplotlib.pyplot as plt

def create_fig_with_n_panels(ncols, nrows, h_ratio = None):
    # now we make a figure
    fig    = plt.figure(figsize=(24, 18));
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

    histos = [stackable.h for stackable in stackables]
    colors = [stackable.sample.color for stackable in stackables]
    labels = [stackable.label for stackable in stackables]
    data_h = data.h
    hep.histplot(histos, color = colors, label = labels, ax = axis, histtype='fill', stack=True, zorder=1)
    axis.scatter(data_h.axes.centers[0][~blind], data_h.values()[~blind], color = 'black', marker='x', s=70, zorder=2)
    axis.legend(ncol=2, loc='best')
    axis.set_ylabel("Number of Events")

    if any(any(h.values()>0) for h in stackables['h']) :
        axis.set_yscale("log")
    plt.setp(axis.get_xticklabels(), visible=False)
    # X-label
    axis.set_xlabel('')
    #Title
    axis.set_title(title)

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

def plot_separation(signal_histo, bkg_histo, axis, signal_color, signal_name):
    signal_copy = signal_histo.copy()
    bkg_copy    = bkg_histo.copy()
    signal_vals = signal_copy.values(flow=True)
    bkg_vals    = bkg_copy.values(flow=True)
    signal_copy *= 1/sum(signal_vals) if sum(signal_vals) > 0 else 0
    bkg_copy    *= 1/sum(bkg_vals)    if sum(bkg_vals)    > 0 else 0

    hep.histplot([signal_copy, bkg_copy], color = [signal_color, 'black'], label = [signal_name, 'Total Background'], ax = axis)

    axis.legend(ncol=1, loc='best')
    axis.set_ylabel("a.u. (Normalised)")

def get_signif_per_bin(signal_h, bkg_h):

    signal_vals  = signal_h.values()
    signal_var   = signal_h.variances()
    bkg_vals     = bkg_h.values()
    bkg_var      = bkg_h.variances()


    sqrt_bkg_vals = np.sqrt(bkg_vals,                      out=np.full_like(signal_h.axes.centers[0], 0), where=bkg_vals>0)
    signficance   = np.divide(signal_vals, sqrt_bkg_vals,  out=np.full_like(signal_h.axes.centers[0], 0), where=sqrt_bkg_vals>0.001)

    err1          = (1/4)*np.divide(bkg_var, bkg_vals**2,   out=np.full_like(signal_h.axes.centers[0], 1e3), where=bkg_vals>0.001)
    err2          = np.divide(signal_var, signal_vals**2,   out=np.full_like(signal_h.axes.centers[0], 1e3), where=signal_vals>0.001)

    signficance_err  = signficance*np.sqrt(err1+err2,      out=np.full_like(signal_h.axes.centers[0], 1e3), where=err1+err2>=0)

    return signficance, signficance_err

def plot_signif_per_bin(signal_h, signif, err, axis, signal_color, signal_name, xlabel, last_ax):


    binedges   = signal_h.axes.edges[0]
    binwidths  = binedges[1:] - binedges[:-1]
    bincenters = signal_h.axes.centers[0]
    color      =  signal_color
    axis.bar(     bincenters, signif, width = binwidths,   color = signal_color, align='center')
    axis.errorbar(bincenters, signif, err, alpha=0.4, color = 'black', linestyle = 'None')

    # Signficance panel y-label
    axis.set_ylabel(f"{signal_name}"+r"$/\sqrt{B}$", rotation=0, fontsize=20, labelpad=70, verticalalignment='center')

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
        axis.set_xlabel(xlabel, fontsize=24)