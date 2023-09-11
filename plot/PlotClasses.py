
from collections import defaultdict

import hist
import mplhep

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpl_patches

from containers.histograms import Histogram
from config.plot_classes import SeparationSettings

import logging
log = logging.getLogger(__name__)

plt.style.use(mplhep.style.ATLAS)
plt.rcParams['axes.linewidth'] = 3
plt.rcParams['font.size'] = 30
plt.rcParams['xtick.major.pad']='10'
plt.rcParams['ytick.major.pad']='10'
plt.rcParams['text.latex.preamble'] = r'\centering'

class CoffeaPlot(object):
    '''
    This class can create the figure, the axes, handle Stacks and RatioPlots and Box
    objects to produce a plot that gets saved to a file.
    '''
    def __init__(self, stacks = [], ratio_plots = [], settings = None, add_auto_text = None):

        # Data
        self.stacks = stacks if isinstance(stacks, list) else [stacks]
        self.ratio_plots = ratio_plots if isinstance(ratio_plots, list) else [ratio_plots]
        self.settings = settings

        if add_auto_text is None:
            self.additional_text = []
        else:
            if not isinstance(add_auto_text, list):
                log.error("Additional text must be a list of list [[text, location]]")
            self.additional_text = add_auto_text


    def make_figure(self):
        fig    = plt.figure(figsize=self.settings.figuresize)
        nrows = len(self.ratio_plots) + 1

        if self.settings.heightratios is None:
            if len(self.ratio_plots) == 0:
                height_ratios = [1]
            else:
                height_ratios =  [3,*[1]*(len(self.ratio_plots))]
        else:
            assert len(self.settings.heightratios) == nrows, f"Number of height ratios ({len(self.settings.heightratios)}) does not match number of axes ({len(self.ratio_plots)})"
            height_ratios = self.settings.heightratios

        gs     = fig.add_gridspec(ncols=1, nrows=nrows, height_ratios=height_ratios, hspace=0.1)
        main_ax     = fig.add_subplot(gs[0, 0])
        rat_axes = []
        for i in range(nrows-1):
            rat_ax = fig.add_subplot(gs[i+1, 0], sharex=main_ax)
            rat_axes.append(rat_ax)

        return fig, main_ax, rat_axes

    def apply_blinder(self, ax, blinder, histograms, binval, binerr):

        # Get the blinded bin indices
        blinded_bins = blinder.get_blinded_bins()
        # Loop over each bin index to be blinded
        for blinded_bin_idx in blinded_bins:
            # Loop over all histograms in the stack plot affected by blinding and nullify the bin contents
            for histogram in histograms:
                histogram.values()[blinded_bin_idx] = binval
                histogram.variances()[blinded_bin_idx] = binerr

            # Get bin edges to shade between
            shade_x1, shade_x2 = histograms[0].axes.edges[0][blinded_bin_idx:blinded_bin_idx+2] # Last index is not inclusive

            # Need to shade twice to get the hatch to show up in legend
            VSpanBox((shade_x1, shade_x2), color='blue', alpha=0.06, linewidth=0).draw(ax)
            # Avoid adding multiple labels to legend
            if blinded_bin_idx == blinded_bins[0]:  label = 'Blinded'
            else:   label = None

            VSpanBox((shade_x1, shade_x2), facecolor='none', edgecolor='grey', hatch="//", alpha=0.5, linewidth=0, label = label).draw(ax)


    def plot_main_canvas(self, main_ax):

        max_bin_contents = []
        # Loop over stacks being overlaid on the plot
        for i, stack in enumerate(self.stacks):

            # Sort stackatinos by sum of bin contents so that biggest stack element goes first
            sorted_stackatinos = sorted(stack.stackatinos, key=lambda stackatino: stackatino.sum.values().sum(), reverse=True)

            # mplhep expects lists of stacks and corresponding settings
            styles = defaultdict(list)
            histograms, labels = [], []

            # A stackatino can be the sum of some yields (stackatino = category, items are samples)
            for stackatino in sorted_stackatinos:
                # Adjust the histgoram that is being plotted if y-axis is normalized
                if not self.settings.main.ynorm:
                    # Just pass the histogram if not normalizing
                    histograms.append(stackatino.sum.h)
                else:
                    # Don't allow log scale if normalizing
                    if self.settings.main.ylog:
                        log.warning("Cannot set log scale when normalizing to unity")
                        self.main.ylog = False
                    # Divide each bin by integral
                    if not all(v == 1e-6 for v in stackatino.sum.h.values()):
                        histograms.append(stackatino.sum.h/stackatino.sum.h.values().sum())
                    else:
                        histograms.append(stackatino.sum.h*0)

                # Add the styling for each stackatino
                for stackitem, style in stackatino.styling.items():
                    styles[stackitem].append(style)

                # Add the label for each stackatino (name of sample)
                labels.append(stackatino.label)

            # Keep track of the largest bin content in each stack to set auto y-axis range
            if stack.stack:
                # If we are summing stackatinos, use largest bin in summed histogram to set ymax
                max_bin_contents.append(max(sum(histogram for histogram in histograms).values()))
            else:
                # If we are not summing stackatinos, use largest bin in any one histogram to set ymax
                max_bin_contents.append(max(max(histogram.values()) for histogram in histograms))

            # If the stack needs to blinded, shade the blinded bins and set the bin contents to 0
            if stack.blinder is not None:
                self.apply_blinder(main_ax, stack.blinder, histograms, 1e-10, 1e-20)

            # Set the x-range while we have the histograms
            xrange = (histograms[0].axes[0].edges[0], histograms[0].axes[0].edges[-1])

            # Plot the stack
            mplhep.histplot(histograms, label = labels, ax = main_ax, histtype=stack.bar_type, stack=stack.stack, flow='hint', **styles)

        return max_bin_contents, xrange

    def decorate_main_canvas(self, main_ax, max_bin_contents, xrange):

        # ==================== X-axis ==================== #
        # If there are ratio plots, don't use an x-axis label on main plot
        if len(self.ratio_plots) != 0:
            plt.setp(main_ax.get_xticklabels(), visible=False)
            main_ax.set_xlabel('')
        else:
            plt.setp(main_ax.get_xticklabels(), visible=True)
            main_ax.set_xlabel(self.stacks[0].stackatinos[0].histograms[0].label, fontsize=self.settings.main.xlabelfontsize)

        # Set the x-axis range
        if self.settings.main.xrange is None:
            main_ax.set_xlim(xrange)
        else:
            main_ax.set_xlim(self.settings.main.xrange)

        # ===================== Y-axis ==================== #
        # Set the y-axis label
        if self.settings.main.ylabel is not None:
            main_ax.set_ylabel(self.settings.main.ylabel, fontsize=self.settings.main.ylabelfontsize)
        else:
            if self.settings.main.ynorm:
                main_ax.set_ylabel('Fraction of events / bin', fontsize=self.settings.main.ylabelfontsize)
            else:
                main_ax.set_ylabel('Number of Events', fontsize=self.settings.main.ylabelfontsize)

        # Set the y-axis scale
        if self.settings.main.ylog:
            main_ax.set_yscale('log')

        # Set the y-axis range
        if self.settings.main.yrange is not None:
            main_ax.set_ylim(self.settings.main.yrange)
        else:
            if self.settings.main.ylog:
                main_ax.set_ylim(1., max(max_bin_contents)*20)
            else:
                main_ax.set_ylim(0., max(max_bin_contents)*1.25)

        # ==================== Add Text to Plot ==================== #
        # Use legends to benifit from auto placement of text and easy locating
        for text in self.settings.main.text + self.additional_text:
            txt, loc = text
            if txt is None and loc is None : continue
            if txt is None: continue
            if loc is None: loc = 'best'

            handle = mpl_patches.Rectangle((0, 0), 1, 1, fc="white", ec="white", lw=0, alpha=0)
            legend = main_ax.legend([handle], [txt], loc=loc, fontsize=self.settings.main.legendfontsize)
            main_ax.add_artist(legend)

        # ==================== Legend ==================== #
        if self.settings.main.legendshow:
            if self.settings.main.legendoutside:
                plt.legend(bbox_to_anchor=(1.04, 1), loc='upper right', ncol=self.settings.main.legendncol, fontsize=self.settings.main.legendfontsize)
            else:
                plt.legend(loc=self.settings.main.legendloc, ncol=self.settings.main.legendncol, fontsize=self.settings.main.legendfontsize)

        # COM notworking
        mplhep.atlas.label(self.settings.status, data=True, lumi=self.settings.lumi, com=self.settings.energy, ax = main_ax, fontsize=30)

    def plot_ratio_canvases(self, ratio_plot, ratio_ax):

        # Loop over ratio items in the ratio plot
        for ratio_item in ratio_plot.ratio_items:

            # Normalise numerators and denominators if the main plot is normalised
            if self.settings.main.ynorm:
                ratio_item.numerator.h   *= 1/ratio_item.numerator.h.values().sum()
                ratio_item.denominator.h *= 1/ratio_item.denominator.h.values().sum()

            # Get the bin centers edges and widths for the ratio plot
            bin_centers = ratio_item.numerator.h.axes[0].centers
            bin_edges   = ratio_item.numerator.h.axes[0].edges
            bin_widths  = (bin_edges[1:] - bin_edges[:-1])

            # Compute ratio values and errors
            ratio_vals = ratio_item.get_ratio_vals()
            ratio_err  = ratio_item.err()

            # Plot the ratio and error bars
            mplhep.histplot(ratio_vals, bins=bin_edges, yerr=ratio_err, label = ratio_item.label, ax = ratio_ax, histtype=ratio_plot.bar_type, stack=ratio_plot.stack, **ratio_item.styling)

            # If this is a DataMC plot, add a relative MC uncertainty band
            if isinstance(ratio_item, DataOverMC):
                # Get the uncertainty band
                mc_err = ratio_item.mc_err()
                # Plot the uncertainty band
                ratio_ax.bar(bin_centers, 2*mc_err, width= bin_widths, bottom=(1.0-mc_err), fill=False, linewidth=0, edgecolor="gray", hatch=3 * "/",)

        # If the stack needs to blinded, shade the blinded bins and set the bin contents to 0
        if ratio_plot.blinder is not None:
            numerators = [ratio_item.numerator.h for ratio_item in ratio_plot.ratio_items]
            self.apply_blinder(ratio_ax, ratio_plot.blinder, numerators, 0, 1e-20)


    def decorate_ratio_canvases(self, ratio_plot, ratio_ax, last_canvas):

        # ================= Legends ==================== #
        if self.settings.ratio.legendshow:
            if self.settings.ratio.legendoutside:
                ratio_ax.legend(bbox_to_anchor=(1.04, 1), loc='upper left', ncol=self.settings.ratio.legendncol, fontsize=self.settings.ratio.legendfontsize)
            else:
                ratio_ax.legend(loc=self.settings.ratio.legend_loc, ncol=self.settings.ratio.legendncol, fontsize=self.settings.ratio.legendfontsize)

        # ================= X-axis ==================== #
        if last_canvas:
            ratio_ax.set_xlabel(self.stacks[0].stackatinos[0].histograms[0].label, fontsize = self.settings.main.xlabelfontsize)
        else:
            plt.setp(ratio_ax.get_xticklabels(), visible=False)
            ratio_ax.set_xlabel('')

        # ================= Y-axis ==================== #

        # Set the y-axis scale
        if self.settings.ratio.ylog:
            ratio_ax.set_yscale('log')

        # Set the y-axis range
        if self.settings.ratio.yrange is not None:
            ratio_ax.set_ylim(self.settings.ratio.yrange)

        # Set the y-axis label
        if ratio_plot.ylabel is not None:
            ratio_ax.set_ylabel(ratio_plot.ylabel, loc='center', verticalalignment='center', labelpad=20, fontsize=self.settings.ratio.ylabelfontsize)
        if self.settings.ratio.ylabel is not None:
            ratio_ax.set_ylabel(self.settings.ratio.ylabel, loc='center', verticalalignment='center', labelpad=20, fontsize=self.settings.ratio.ylabelfontsize)

        # ==================== Grid ==================== #
        ratio_ax.grid(True)


    def plot(self, outpath):

        fig, main_ax, rat_axes = self.make_figure()

        max_bin_contents, xrange = self.plot_main_canvas(main_ax)

        self.decorate_main_canvas(main_ax, max_bin_contents, xrange)

        for i, ratio_plot in enumerate(self.ratio_plots):
            ratio_ax = rat_axes[i]
            if len(ratio_plot.ratio_items) == 0:    continue
            last_canvas = False
            if i == len(self.ratio_plots)-1:        last_canvas = True
            self.plot_ratio_canvases(ratio_plot, ratio_ax)
            self.decorate_ratio_canvases(ratio_plot, ratio_ax, last_canvas)

        filename = self.stacks[0].plotid.variable + '__' + self.stacks[0].plotid.region + '__' + self.stacks[0].plotid.rescale
        plt.savefig(f"{outpath}/{filename}.pdf", bbox_inches='tight')
        plt.close('all')


class PieChart(CoffeaPlot):
    pass

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

    def __init__(self, bar_type, error_type = 'stat', stack=True, ylabel = None, blinder = None, plottersettings = None):


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
        self.stack = stack

        self.ylabel = ylabel

        self.blinder = blinder

        if plottersettings is not None:
            self.plotid = PlotIdentifier(plottersettings)
        else:
            raise ValueError("Must specify an identifier for a stack")

class RatioPlot(DistWithUncObjects):
    def __init__(self, ratio_items, bar_type = 'step', error_type = 'stat', stack=False, ylabel=None, blinder = None, plottersettings = None):

        '''
        Create a RatioPlot object.

        This class can hold multiple distributions that are plotted in a ratio panel
        '''
        self.ratio_items = []

        DistWithUncObjects.__init__(self, bar_type, error_type, stack=stack, ylabel=ylabel, blinder=blinder, plottersettings=plottersettings)

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

    def err(self):
        ratio_vals = self.get_ratio_vals()
        numerator_vals = self.numerator.values()
        numerator_variances = self.numerator.variances()

        denominator_vals = self.denominator.values()
        denominator_variances = self.denominator.variances()

        err_part1 = np.divide(numerator_variances, numerator_vals**2, out=np.full_like(numerator_variances, 0), where=(numerator_vals>1e-4))
        err_part2 = np.divide(denominator_variances**2 * denominator_vals, denominator_vals**4, out=np.full_like(numerator_variances, 0), where=(denominator_vals>1e-4))

        err = ratio_vals*np.sqrt(err_part1 + err_part2, out=np.full_like(numerator_variances, 0), where=(numerator_vals>1e-4) & (denominator_vals>1e-4))

        return err

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

    def __init__(self, stackatinos, bar_type = 'filled', error_type = 'stat', stack=True, ylabel=None, blinder = None, plottersettings = None):

        # List of stackatinos
        self.stackatinos = stackatinos
        DistWithUncObjects.__init__(self, bar_type, error_type, stack=stack, ylabel=ylabel, blinder=blinder, plottersettings=plottersettings)

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
        return s_over_sqrtb > self.threshold

    def get_blinded_bins(self):
        return [bin_idx for bin_idx, bin_is_blinded in enumerate(self.get_blinding()) if bin_is_blinded]


class PlotterSettings(object):
    def __init__(self, variable, region, rescale):
        self.region = region
        self.variable = variable
        self.rescale = rescale

        # Processed attributes
        self.backgrounds_histos = None
        self.signals_histos = None
        self.tot_signals_histo = None
        self.tot_backgrounds_histo = None
        self.data_histo = None
        self.total_mc_histo = None
        self.category_to_sample_histos= None
        self.region_targets_histos = None


        self.mc_stack = None
        self.data_stack = None
        self.data_over_mc_ratio = None
        self.mc_over_mc_ratio = None
        self.signif_ratios  = None
        self.sep_stack = None


class PlotIdentifier(object):
    def __init__(self, plottersettings):
        self.variable = plottersettings.variable.name
        self.region   = plottersettings.region.name
        self.rescale  = plottersettings.rescale.name