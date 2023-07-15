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
