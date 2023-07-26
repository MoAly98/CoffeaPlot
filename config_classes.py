from logger import ColoredLogger as logger
import importlib.util
from inspect import getmembers, isfunction, isroutine
import os, re

class CoffeaPlotSettings(object):

    log = logger()

    def __init__(self):

        self.dumpdir = None
        self.ntuplesdirs = None
        self.trees = None
        self.mcweight = None
        self.samples_list = None
        self.regions_list = None
        self.variables_list = None
        self.rescales_list = None

        # Optional
        self.inputhistos = None
        self.helpers = None
        self.runprocessor = None
        self.runplotter = None
        self.skipnomrescale = None
        self.loglevel = None
        self.makeplots = None

        # Processed attributes
        self.functions = None
        self.tree_to_dir = None

        # Plot Settings
        self.datamc_plot_settings = None
        self.mcmc_plot_settings = None
        self.significance_plot_settings = None

    def __getitem__(self, item):
        return getattr(self, item)

    def setup_helpers(self):

        # Set up logger
        log = logger()
        log.info("Setting up helper functions")

        # =========== Set up helpers =========== #
        helpers = self.helpers
        functions = {}
        if helpers is not None:
            for i, helper in enumerate(helpers):
                log.debug(f"Importing helper functions from {helper}")
                spec = importlib.util.spec_from_file_location(f'my_module_{i}', helper)
                my_helper = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(my_helper)
                methods = dict((x, y) for x, y in getmembers(my_helper, isfunction))
                functions.update(methods)

        self.functions = functions

    def setup_inputpaths(self):

        # Set up logger
        log = logger()
        log.info("Running checks on input paths")

        # =========== Checks on input direcotries =========== #
        if self.ntuplesdirs is not None:
            for ntupsdir in self.ntuplesdirs:
                if not os.path.exists(ntupsdir):
                    log.error(f'Ntuple directory {ntupsdir} does not exist')

        if self.inputhistos is not None:
            if self.runprocessor:
                log.warning(f'You provided a histogram files {self.inputhistos} but you are running the processor. The histogram file will be ignored')
                self.inputhistos = None
            for inhistofile in self.inputhistos:
                if not os.path.exists(inhistofile):
                    log.error(f'Input histogram file {inhistofile} does not exist')



    def setup_outpaths(self):

        # Set up logger
        log = logger()
        log.info("Preparing output paths")

        # =========== Prepare output directory =========== #
        os.makedirs(self.dumpdir, exist_ok=True)

        self.tree_to_dir = { tree: {
                                'datadir': None,
                                'mcmcdir': None,
                                'datamcdir': None,
                                'separationdir': None,
                                'significancedir': None,
                                'tablesdir': None,
                                }
                        for tree in self.trees
                        }

        for tree in self.trees:
            # ==== Data ==== #
            datadir = f'{self.dumpdir}/data/'
            self.tree_to_dir[tree]['datadir'] = datadir
            os.makedirs(datadir, exist_ok=True)

            # ==== Plots ==== #
            if 'SIGNIF' in self.makeplots:
                significancedir = f'{self.dumpdir}/plots/{tree}/Significance'
                self.tree_to_dir[tree]['significancedir'] = significancedir
                os.makedirs(significancedir, exist_ok=True)
            if 'MCMC' in self.makeplots:
                mcmcdir = f'{self.dumpdir}/plots/{tree}/MCMC'
                self.tree_to_dir[tree]['mcmcdir'] = mcmcdir
                os.makedirs(mcmcdir, exist_ok=True)
            if 'DATAMC' in self.makeplots:
                datamcdir = f'{self.dumpdir}/plots/{tree}/DataMC'
                self.tree_to_dir[tree]['datamcdir'] = datamcdir
                os.makedirs(datamcdir, exist_ok=True)

            # === Tables === #
            tablesdir = f'{self.dumpdir}/tables/{tree}'
            self.tree_to_dir[tree]['tablesdir'] = tablesdir
            os.makedirs(tablesdir, exist_ok=True)


class GeneralPlotSettings(object):
    def __init__(self):
        self.figure_size = None
        self.lumi = None
        self.energy  = None
        self.experiment = None
        self.plot_status = None
        self.plot_title = None
        self.height_ratios = None

    def __getitem__(self, item):
        return getattr(self, item)

class CanvasSettings(object):
    def __init__(self):
        self.ylabel = None
        self.ylog = None
        self.yrange = None
        self.legend_show = None
        self.legend_outside = None
        self.legend_loc = None
        self.legend_ncol = None
        self.legend_fontsize = None

    def __getitem__(self, item):
        return getattr(self, item)

class MainCanvasSettings(CanvasSettings):
    def __init__(self, maincanvas):
        self.__dict__ = maincanvas.__dict__.copy()
        self.ynorm = None

class RatioCanvasSettings(CanvasSettings):
    '''
    This class is for readbiblity purposes only, can be used in future for ratio canvas settings
    that are not main canvas settings
    '''
    def __init__(self, maincanvas):
        self.__dict__ = maincanvas.__dict__.copy()


class PlotWithRatioSettings(object):
    def __init__(self, main_canvas_settings, ratio_canvas_settings):
        self.main = main_canvas_settings
        self.ratio = ratio_canvas_settings

class DataMCSettings(PlotWithRatioSettings):
    def __init__(self, main_canvas_settings, ratio_canvas_settings):
        self.data = None
        self.mc = None
        super(DataMCSettings, self).__init__(main_canvas_settings, ratio_canvas_settings)

class MCMCSettings(PlotWithRatioSettings):
    def __init__(self, main_canvas_settings, ratio_canvas_settings):
        self.refsamples = None
        super(MCMCSettings, self).__init__(main_canvas_settings, ratio_canvas_settings)

class SignificanceSettings(PlotWithRatioSettings):
    def __init__(self, main_canvas_settings, ratio_canvas_settings):
        super(SignificanceSettings, self).__init__(main_canvas_settings, ratio_canvas_settings)