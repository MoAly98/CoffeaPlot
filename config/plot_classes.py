import logging
log = logging.getLogger(__name__)

class GeneralPlotSettings(object):

    """
    This class contains all the settings that apply to all plots, but can be overwritten by
    specialised plot settings for the various plot types. It holds attributes relevant for
    all panels of the plot, such as figure size, title, etc.
    """
    def __init__(self):
        # Figure organisation
        self.figuresize = None
        self.figuretitle = None
        self.status = None
        self.heightratios = None
        # Text on Figure
        self.lumi = None
        self.energy  = None
        self.experiment = None

    def __getitem__(self, item):
        return getattr(self, item)

class PlotWithRatioSettings(GeneralPlotSettings):
    """
    Plots that have a main + ratio panels have all settings of a GeneralPlotSettings object,
    but also have settings for the main and ratio panels individually.
    """
    def __init__(self, main_canvas_settings = None, ratio_canvas_settings = None):
        self.main  = main_canvas_settings
        self.ratio = ratio_canvas_settings
        super(PlotWithRatioSettings, self).__init__()

class DataMCSettings(PlotWithRatioSettings):
    """
    DataMC plots have all settings of a PlotWithRatioSettings object, but also have settings
    for the which sample should be used as data and which as MC.
    """
    def __init__(self):
        self.data = None
        self.mc   = None
        super(DataMCSettings, self).__init__()

class MCMCSettings(PlotWithRatioSettings):
    """
    MCMC plots have all settings of a PlotWithRatioSettings object, but also have settings
    for the reference samples to which the other samples are compared to.
    """
    def __init__(self):
        self.refsamples = None
        super(MCMCSettings, self).__init__()

class SeparationSettings(PlotWithRatioSettings):
    """
    Separation plots have all settings of a PlotWithRatioSettings object, but also have settings
    to allow writing the separation values on the plot.
    """
    def __init__(self):
        self.writesep = None
        self.seploc   = None
        super(SeparationSettings, self).__init__()

class PanelSettings(object):
    """
    This class contains all the settings that apply to a single panel on a plot. It holds
    attributes that apply to both panels of a plot, such as y-axis range, log scale, etc.
    """
    def __init__(self):

        self.ylabel         = None
        self.ylog           = None
        self.yrange         = None
        self.xrange         = None
        self.xlog           = None
        self.xlabelfontsize = None
        self.legendshow     = None
        self.legendoutside  = None
        self.legendloc      = None
        self.legendncol     = None
        self.legendfontsize = None
        self.text           = None

    def __getitem__(self, item):
        return getattr(self, item)

class MainPanelSettings(PanelSettings):
    """
    MainPanelSettings have all settings of a PanelSettings object, but also have settings
    that don't apply to the ratio panel, such as the normalisation of the y-axis.
    """
    def __init__(self):
        self.ynorm = None
        super(MainPanelSettings, self).__init__()

