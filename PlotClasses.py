import numpy as np
import hist
from classes import Histogram
import matplotlib.pyplot as plt
import mplhep
from collections import defaultdict

plt.style.use(mplhep.style.ATLAS)
plt.rcParams['axes.linewidth'] = 3
plt.rcParams.update({'font.size': 20})
plt.rcParams['xtick.major.pad']='10'
plt.rcParams['ytick.major.pad']='10'

class CoffeaPlot(object):
    '''
    This class can create the figure, the axes, handle Stacks and RatioPlots and Box
    objects to produce a plot that gets saved to a file.
    '''
    def __init__(self, stacks = [], ratio_plots = [], blinder = None, **settings):

        # Data
        self.stacks = stacks if isinstance(stacks, list) else [stacks]
        self.ratio_plots = ratio_plots if isinstance(ratio_plots, list) else [ratio_plots]

        # ========== General Figure ========== #
        self.figure_size = None
        self.figure_title = None
        # Ratio of heights of main plot and all ratio plots


        if len(self.ratio_plots) == 0:
            self.height_ratios = [1]
        else:
            self.height_ratios =  [3,*[1]*(len(self.ratio_plots)+1-1)]
        # ATLAS?
        self.experiment = None
        # Internal, Simulation, Prelimary, etc.
        self.plot_status = None
        # In ifb
        self.lumi = None
        # In TeV
        self.com = None
        # Region name, scaling
        self.subtext = None
        # Save to what file
        self.outfile = None
        # Event selection text
        self.selection = None

        # ========== Ratio Plots ========= #
        self.ratio_yrange = None
        self.ratio_ylog   = None
        self.ratio_ylabel = None
        #self.ratio_blinder = None

        # ========== Main Plot =========== #
        self.main_yrange = None
        self.main_ylog   = None
        self.main_ylabel = None
       # self.main_blinder = None

        # ========== Set plot settings ============= #

        for key, value in settings.items():
            setattr(self, key, value)


        # TODO:: Add support for rebinning by specifying how to merge bins
        self.new_edges = None

    def plot(self):

        fig    = plt.figure(figsize=self.figure_size)
        nrows = len(self.ratio_plots) + 1
        gs     = fig.add_gridspec(ncols=1, nrows=nrows, height_ratios=self.height_ratios, hspace=0.1)
        main_ax     = fig.add_subplot(gs[0, 0])
        rat_axes = []
        for i in range(nrows-1):
            rat_ax = fig.add_subplot(gs[i+1, 0], sharex=main_ax)
            rat_axes.append(rat_ax)

        max_bin_contents = []
        for i, stack in enumerate(self.stacks):


            sorted_stackatinos = sorted(stack.stackatinos, key=lambda stackatino: stackatino.sum.values().sum(), reverse=True)

            styles = defaultdict(list)
            histograms, colors, labels = [], [], []
            for stackatino in sorted_stackatinos:
                histograms.append(stackatino.sum.h)
                for key, value in stackatino.styling.items():
                    styles[key].append(value)

                #colors.append(stackatino.color())
                labels.append(stackatino.label)
            nostack = False
            if not nostack:
                max_bin_contents.append(max(sum(histogram for histogram in histograms).values()))
            else:
                max_bin_contents.append(max(max(histogram.values()) for histogram in histograms))


            if stack.blinder is not None:
                blinded_bins = stack.blinder.get_blinded_bins()
                for blinded_bin_idx in blinded_bins:
                    for histogram in histograms:
                        histogram.values()[blinded_bin_idx] = 1e-10
                        histogram.variances()[blinded_bin_idx] = 1e-20

                    shade_x1, shade_x2 = histograms[0].axes.edges[0][blinded_bin_idx:blinded_bin_idx+2] # Last index is not inclusive

                    VSpanBox((shade_x1, shade_x2), color='blue', alpha=0.06, linewidth=0).draw(main_ax)

                    if blinded_bin_idx == blinded_bins[0]:
                        label = 'Blinded'
                    else:
                        label = None
                    VSpanBox((shade_x1, shade_x2), facecolor='none', edgecolor='grey', hatch="//", alpha=0.5, linewidth=0, label = label).draw(main_ax)

            mplhep.histplot(histograms, label = labels, ax = main_ax, histtype=stack.bar_type, stack=True, **styles)

        if len(self.ratio_plots) != 0:
            plt.setp(main_ax.get_xticklabels(), visible=False)
            main_ax.set_xlabel('')

            main_ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left", ncol=2)

        if self.main_ylabel is not None:
            main_ax.set_ylabel(self.main_ylabel)

        if self.main_ylog is not None:
            main_ax.set_yscale('log')

        if self.main_yrange is not None:
            main_ax.set_ylim(self.main_yrange)
        else:
            if self.main_ylog is not None:
                main_ax.set_ylim(1., max(max_bin_contents)*20)
            else:
                main_ax.set_ylim(0., max(max_bin_contents)*2.)

        # COM notworking
        mplhep.atlas.label(self.plot_status, data=True, lumi=self.lumi, com=self.com, ax = main_ax, fontsize=29)




        for i, ratio_plot in enumerate(self.ratio_plots):
            ratio_ax = rat_axes[i]

            if ratio_plot.blinder is not None:
                blinded_bins = ratio_plot.blinder.get_blinded_bins()
                blinding_bool = ratio_plot.blinder.get_blinding()

                for blinded_bin_idx in blinded_bins:

                    shade_x1, shade_x2 = histograms[0].axes.edges[0][blinded_bin_idx:blinded_bin_idx+2] # Last index is not inclusive
                    VSpanBox((shade_x1, shade_x2), color='blue', alpha=0.06, linewidth=0).draw(ratio_ax)

                    if blinded_bin_idx == blinded_bins[0]:
                        label = 'Blinded'
                    else:
                        label = None
                    VSpanBox((shade_x1, shade_x2), facecolor='none', edgecolor='grey', hatch="//", alpha=0.5, linewidth=0, label = label).draw(ratio_ax)

            for ratio_item in ratio_plot.ratio_items:


                bin_centers = ratio_item.numerator.h.axes[0].centers
                bin_edges   = ratio_item.numerator.h.axes[0].edges
                bin_widths  = (bin_edges[1:] - bin_edges[:-1])

                ratio_vals = ratio_item.get_ratio_vals()
                ratio_err  = ratio_item.err()
                if ratio_plot.blinder is not None:
                    ratio_vals[blinding_bool] = 1e6
                    ratio_err[blinding_bool] = 0

                mplhep.histplot(ratio_vals, bins=bin_edges, yerr=ratio_err, label = ratio_item.label, ax = ratio_ax, histtype=ratio_plot.bar_type, stack=False, **ratio_item.styling)

                if isinstance(ratio_item, DataOverMC):
                    mc_err = ratio_item.mc_err()
                    ratio_ax.bar(bin_centers, 2*mc_err, width= bin_widths, bottom=(1.0-mc_err), fill=False, linewidth=0, edgecolor="gray", hatch=3 * "/",)
                    ratio_ax.set_ylim((0.8,1.2))
                    ratio_ax.grid(True)



            if i != len(self.ratio_plots) - 1:
                plt.setp(ratio_ax.get_xticklabels(), visible=False)
            else:
                ratio_ax.set_xlabel(ratio_plot.ratio_items[0].numerator.label)

            if self.ratio_ylabel is not None:
                ratio_ax.set_ylabel(self.ratio_ylabel, loc='center', labelpad=20)



        plt.savefig(self.outfile, bbox_inches='tight')
        plt.close('all')


class StylableObject(object):

    VALID_STYLE_SETTINGS = ["facecolor", "linestyle", "linewidth", "color", "edgecolor", "markersize", "marker", "fill", "alpha", "hatch"]

    def __init__(self, **styling):
        for style in styling:
            if style not in self.VALID_STYLE_SETTINGS:
                raise ValueError(f"Invalid style setting: {style}, allowed styles are: {self.VALID_STYLE_SETTINGS}")
        self.styling = styling

    def facecolor(self):
        return self.styling.get('facecolor', None)

    def color(self):
        return self.styling.get('color', None)

    def edgecolor(self):
        return self.styling.get('edgecolor', None)

    def linewidth(self):
        return self.styling.get('linewidth', None)

    def linestyle(self):
        return self.styling.get('linestyle', None)

    def fill(self):
        return self.styling.get('fill', None)

    def alpha(self):
        return self.styling.get('alpha', None)

    def hatch(self):
        return self.styling.get('hatch', None)

class DistWithUncObjects(object):

    # points can be used for data
    ALLOW_BAR_TYPES = ["step", "stepfilled", "points"]
    SUPPORT_BAR_TYPES = ["stepfilled", "points", "step"]
    ALLOW_ERROR_TYPES = ["none", "stat", "syst", "stat"]
    SUPPORT_ERROR_TYPES = ["none", "stat"]

    TO_MPL = {'stepfilled': 'fill', 'points': 'errorbar', 'step': 'step'}

    def __init__(self, bar_type, error_type = 'stat', blinder = None, combo = None):


        if bar_type not in self.ALLOW_BAR_TYPES:
            raise ValueError(f"Invalid stack type: {bar_type}")
        if bar_type not in self.SUPPORT_BAR_TYPES:
            raise NotImplementedError(f"Unsupported stack type: {bar_type}")
        if error_type not in self.ALLOW_ERROR_TYPES:
            raise ValueError(f"Invalid stack error type: {error_type}")
        if error_type not in self.SUPPORT_ERROR_TYPES:
            raise NotImplementedError(f"Unsupported stack error type: {error_type}")

        self.bar_type = self.TO_MPL[bar_type]
        self.error_type = error_type

        self.blinder = blinder

        if combo is not None:

            assert 'variable' in combo, 'Must specify a variable to identify a plot'
            assert 'region' in combo, 'Must specify a region to identify a plot'
            assert 'rescale' in combo, 'Must specify a rescale to identify a plot'
            self.combo = PlotIdentifier(combo)
        else:
            raise ValueError("Must specify an identifier for a stack")

class PlotIdentifier(object):
    def __init__(self, identifier_dict):
        self.variable = identifier_dict['variable']
        self.region = identifier_dict['region']
        self.rescale = identifier_dict['rescale']

class RatioPlots(object):
    '''
    A colleciton of ratio plots, when one wants multiple ratio panels.
    '''
    pass

class RatioPlot(DistWithUncObjects):
    def __init__(self, ratio_items, bar_type = 'step', error_type = 'stat', blinder = None, combo = None):

        '''
        Create a RatioPlot object.

        This class can hold multiple distributions that are plotted in a ratio panel
        '''
        self.ratio_items = []

        DistWithUncObjects.__init__(self, bar_type, error_type, blinder=blinder, combo=combo)

    def append(self, ratio_item):
        self.ratio_items.append(ratio_item)


class RatioItem(StylableObject):
    def __init__(self, numerator, denominator, label = None, ylabel = '', **styling):

        '''
        Create a RatioItem object.

        This class can hold one distribution that is plotted in a ratio panel
        '''
        self.numerator = numerator
        self.denominator = denominator
        self.label = label

        StylableObject.__init__(self, **styling)

    def get_ratio_vals(self):
        numerator_vals = self.numerator.values()
        denominator_vals = self.denominator.values()
        ratio_vals = np.divide(numerator_vals, denominator_vals,  out=np.full_like(denominator_vals, 0), where= (denominator_vals>1e-4))

        return ratio_vals

class DataOverMC(RatioItem):
    def __init__(self, data, mc, label = None, ylabel = 'Data/MC', **styling):
        RatioItem.__init__(self, data, mc, label, ylabel, **styling)

    def data_err(self):
        # Data Points
        data = self.numerator.values()
        data_variances = self.numerator.variances()
        mc = self.denominator.values()

        err_data    = np.sqrt(data_variances, out = np.full_like(data_variances, 0), where = (data_variances >=0))
        err         = np.divide(err_data, mc, out = np.full_like(err_data,1e3), where = (mc > 0))

        return err

    def mc_err(self):

        mc = self.denominator.values()
        mc_variances = self.denominator.variances()

        # MC Uncertainty band
        err_mc      = np.sqrt(mc_variances, out = np.full_like(mc_variances, 0), where = (mc_variances >=0))
        err = np.divide(err_mc, mc, out = np.full_like(mc, 1e3), where = (mc > 0))

        return err

    def err(self):
        # Need to keep track of this when plotting!
        return self.data_err()

class Significance(RatioItem):

    def __init__(self, signal, bkg, label = None, ylabel = '', **styling):

        #========= Save the background for error computation =========#
        self.bkg = bkg

        bkg_vals = bkg.values()
        bkg_variances = bkg.variances()
        sqrt_bkg_vals = np.sqrt(bkg_vals, out=np.full_like(bkg_vals, 0), where=(bkg_vals>0) )
        sqrt_bkg_variances = np.divide(bkg_variances, 4*sqrt_bkg_vals, out=np.full_like(bkg_vals, 0), where=(bkg_vals>0) )

        sqrt_bkg_h = hist.Hist.new.Var(bkg.h.axes[0].edges, name = bkg.name, label=bkg.label, flow=True).Weight()
        sqrt_bkg_h[...] = np.stack([sqrt_bkg_vals, sqrt_bkg_variances], axis=-1)

        sqrt_bkg_histo = Histogram(bkg.name, sqrt_bkg_h, bkg.sample, bkg.region, bkg.rescale)

        better_ylabel = fr'{signal.sample}/$\sqrt(B)$'

        RatioItem.__init__(self, signal, sqrt_bkg_histo, label, better_ylabel, **styling)

    def err(self):

        signficance   = self.get_ratio_vals()

        signal_vals      = self.numerator.values()
        signal_variances = self.numerator.variances()

        bkg_vals    = self.bkg.values()
        bkg_variances    = self.bkg.variances()

        err_part1   = (1/4)*np.divide(bkg_variances, bkg_vals**2,  out=np.full_like(signal_vals, 1e3), where=(bkg_vals>1e-4))
        err_part2   = np.divide(signal_variances, signal_vals**2,  out=np.full_like(signal_vals, 1e3), where=(signal_vals>1e-4))

        err  = signficance*np.sqrt(err_part1+err_part2, out=np.full_like(signal_vals, 1e3), where=(err_part1+err_part2>=0))

        return err

class Stack(DistWithUncObjects):
    '''
    A COLLECTION OF Stackatinos.
    '''

    def __init__(self, stackatinos, bar_type = 'filled', error_type = 'stat', blinder = None, combo = None):

        # List of stackatinos
        self.stackatinos = stackatinos
        DistWithUncObjects.__init__(self, bar_type, error_type, blinder=blinder, combo=combo)

    def append(self, stackatino):
        self.stackatinos.append(stackatino)

class Stackatino(StylableObject):
    '''
    This is a proxy to an item on a stack plot (within a stack). For example this
    can be a histogram.
    '''
    def __init__(self, histograms, label = None, **styling):

        self.histograms = histograms
        self.label = label
        self.sum = None

        StylableObject.__init__(self, **styling)

    def append(self, histogram):
        self.histograms.append(histogram)

    def sum_histograms(self):
        self.sum =  sum(self.histograms)
        return self

    # def __repr__(self):
    #     return f"<Stackatino {self.label}: {', '.join([h for h in self.histograms])}>"


class SpanBox(StylableObject):
    '''
    Can be used to draw blinding boxes or shade areas of plot
    '''
    def __init__(self, pos: tuple, **styling):
        self.pos = pos
        StylableObject.__init__(self, **styling)

class HSpanBox(SpanBox):

    def __init__(self, pos: tuple, **styling):
        SpanBox.__init__(self, pos, **styling)

    def draw(self, ax):
        ax.axhspan(*self.pos, **self.styling)

class VSpanBox(SpanBox):

    def __init__(self, pos: tuple, label = None, **styling):
        self.label = label
        SpanBox.__init__(self, pos, **styling)

    def draw(self, ax):
        ax.axvspan(*self.pos, label=self.label, **self.styling)


class Blinder(object):
    def __init__(self, signal_h, background_h, threshold):
        self.sig = signal_h
        self.bkg = background_h
        self.threshold = threshold

    def get_blinding(self):
        signal_vals  = self.sig.values()
        bkg_vals     = self.bkg.values()
        sqrt_bkg     = np.sqrt(bkg_vals, out = np.full_like(bkg_vals, 0), where = bkg_vals>=0)
        s_over_sqrtb = np.divide(signal_vals,  bkg_vals, out = np.full_like(bkg_vals, 0),  where = bkg_vals>0)
        #print(s_over_sqrtb)
        return s_over_sqrtb > self.threshold

    def get_blinded_bins(self):
        return [bin_idx for bin_idx, bin_is_blinded in enumerate(self.get_blinding()) if bin_is_blinded]