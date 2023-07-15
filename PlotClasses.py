import numpy as np
import hist
from classes import Histogram

class CoffeaPlot(object):
    '''
    This class can create the figure, the axes, handle Stacks and RatioPlots and Box
    objects to produce a plot that gets saved to a file.
    '''
    pass

class StylableObject(object):

    VALID_STYLE_SETTINGS = ["linestyle", "linewidth", "color", "edgecolor", "markersize", "marker", "fill", "alpha", "hatch"]

    def __init__(self, **styling):
        for style in styling:
            if style not in self.VALID_STYLE_SETTINGS:
                raise ValueError(f"Invalid style setting: {style}, allowed styles are: {self.VALID_STYLE_SETTINGS}")
        self.styling = styling

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

    def __init__(self, bar_type, error_type = 'stat', blinder = None):
        self.bar_type = bar_type
        self.error_type = error_type

        if bar_type not in self.ALLOW_BAR_TYPES:
            raise ValueError(f"Invalid stack type: {bar_type}")
        if bar_type not in self.SUPPORT_BAR_TYPES:
            raise NotImplementedError(f"Unsupported stack type: {bar_type}")
        if error_type not in self.ALLOW_ERROR_TYPES:
            raise ValueError(f"Invalid stack error type: {error_type}")
        if error_type not in self.SUPPORT_ERROR_TYPES:
            raise NotImplementedError(f"Unsupported stack error type: {error_type}")

        self.blinder = blinder

class RatioPlots(object):
    '''
    A colleciton of ratio plots, when one wants multiple ratio panels.
    '''
    pass

class RatioPlot(DistWithUncObjects):
    def __init__(self, ratio_items = [], bar_type = 'step', error_type = 'stat'):

        '''
        Create a RatioPlot object.

        This class can hold multiple distributions that are plotted in a ratio panel
        '''
        self.ratio_items = []

        DistWithUncObjects.__init__(self, bar_type, error_type)

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

    def get_ratio(self):
        numerator_vals = self.numerator.values()
        denominator_vals = self.denominator.values()

        return  np.divide(numerator_vals, denominator_vals,  out=np.full_like(denominator_vals, 0), where= (denominator_vals>1e-4))

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
        return self.data_err(), self.mc_err()

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

        signficance   = self.get_ratio()

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

    def __init__(self, stackatinos=[], bar_type = 'filled', error_type = 'stat'):

        # List of stackatinos
        self.stackatinos = stackatinos
        DistWithUncObjects.__init__(self, bar_type, error_type)

    def append(self, stackatino):
        self.stackatinos.append(stackatino)

class Stackatino(StylableObject):
    '''
    This is a proxy to an item on a stack plot (within a stack). For example this
    can be a histogram.
    '''
    VALID_STYLE_SETTINGS = ["color", "edgecolor", "linewidth", "linestyle", "fill", "alpha", "hatch"]

    def __init__(self, histograms = [], label = None, **styling):

        self.histograms = histograms
        self.label = label

        StylableObject.__init__(self, **styling)

    def append(self, histogram):
        self.histograms.append(histogram)

    def __repr__(self):
        return f"<Stackatino {self.label}: {', '.join([h for h in self.histograms])}>"


class SpanBox(StylableObject):
    '''
    Can be used to draw blinding boxes or shade areas of plot
    '''
    def __init__(self, pos: tuple, **styling):
        self.pos = pos
        StylableObject.__init__(self, **styling)

class VSpanBox(SpanBox):

    def __init__(self, pos: tuple, **styling):
        SpanBox.__init__(self, pos, **styling)

    def draw(self, ax):
        ax.axvspan(*self.pos, **self.styling)

class VSpanBox(SpanBox):

    def __init__(self, pos: tuple, **styling):
        SpanBox.__init__(self, pos, **styling)

    def draw(self, ax):
        ax.axhspan(*self.pos, **self.styling)


class Blinder(object):
    def __init__(self, signal_h, background_h, threshold):
        self.sig = signal_h
        self.bkg = background_h
        self.threshold = threshold

    def get_blinding(self):
        signal_vals = self.sig.values()
        bkg_vals    = self.bkg.values()
        sqrt_bkg    = np.sqrt(bkg_vals, out = np.full_like(bkg_vals, 0), where = bkg_vals>=0)
        s_over_sqrtb    = np.divide(signal_vals,  bkg_vals, out = np.full_like(bkg_vals, 0),  where = bkg_vals>0)
        return s_over_sqrtb > threshold
