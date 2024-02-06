# === Python Imports === #
import importlib.util
from inspect import getmembers, isfunction, isroutine
import os, re
import logging
log = logging.getLogger(__name__)

class CoffeaPlotSettings(object):
    """
    Class to hold all the settings that steer the execution of the CoffeaPlot
    package. The settings are read from a config file, and then saved as
    attributes of this class.
    """
    def __init__(self):

        # Mandatory
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

        # Processed attributes (not read from config)
        self.functions = None
        self.tree_to_dir = None

        # Plot Settings (not read from config)
        self.datamc_plot_settings = None
        self.mcmc_plot_settings = None
        self.significance_plot_settings = None
        self.separation_plot_settings = None
        self.piechart_plot_settings = None
        self.heatmap_plot_settings = None

    def __getitem__(self, item):
        return getattr(self, item)

    def setup_helpers(self):
        """
        Import helper functions from external module specified in config
        and save them as a dict of function name to function object.
        """

        log.info("Setting up helper functions")
        # Paths to helper functions modules
        helpers = self.helpers
        # Dictionary to hold helper functions
        functions = {}
        # If the user specified helper functions modules
        if helpers is not None:
            # Loop over the modules
            for i, helper in enumerate(helpers):
                # Import the module
                log.debug(f"Importing helper functions from {helper}")
                spec = importlib.util.spec_from_file_location(f'my_module_{i}', helper)
                my_helper = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(my_helper)
                # Add the functions to the dictionary
                methods = dict((x, y) for x, y in getmembers(my_helper, isfunction))
                functions.update(methods)

        self.functions = functions

    def setup_inputpaths(self):
        """
        Check that all input paths used in config general settings exist and are valid.
        This checks the ntuples directories and the input histogram files, in
        case the user wants to run the plotter directly.
        """
        log.info("Running checks on input paths from general settings")

        # If n-tuples directories are specified, check them
        if self.ntuplesdirs is not None:
            for ntupsdir in self.ntuplesdirs:
                if not os.path.exists(ntupsdir):
                    log.error(f'Ntuple directory {ntupsdir} does not exist')

        # If the user wants to run the processor, warn them that the histogram files will be ignored
        if self.runprocessor:
            if self.inputhistos is not None:
                log.warning(f'You provided a histogram files {self.inputhistos} but you are running the processor. The histogram file will be ignored')
            self.inputhistos = None
        # If input histogram files are specified, check them
        if self.inputhistos is not None:
            # If the user wants to run the plotter, check that the histogram files exist
            for inhistofile in self.inputhistos:
                if not os.path.exists(inhistofile):
                    log.error(f'Input histogram file {inhistofile} does not exist')

        # If the user wants to run the plotter only, check that they provided input histogram files
        if self.runplotter and not self.runprocessor and self.inputhistos is None:
            log.error('You are running the plotter only but you did not provide any input histogram files')

    def setup_outpaths(self):
        """
        Prepare the output paths from the general settings. This creates the
        directory structure where the output plots and tables will be saved.

        """
        log.info("Preparing output paths from general settings")
        # Create the directory where everything will be saved
        os.makedirs(self.dumpdir, exist_ok=True)

        # Prepare trees to directories mapping
        self.tree_to_dir = { tree: {
                                'datadir': None,
                                'mcmcdir': None,
                                'datamcdir': None,
                                'separationdir': None,
                                'significancedir': None,
                                'tablesdir': None,
                                'effdir': None,
                                'piechartdir': None,
                                'heatdir': None
                                }
                        for tree in self.trees
                        }

        # Loop over the trees
        for tree in self.trees:

            # ========= Create the directory to store data from processor ========= #
            datadir = f'{self.dumpdir}/data/'
            self.tree_to_dir[tree]['datadir'] = datadir
            os.makedirs(datadir, exist_ok=True)

            # ==== Create the directories to store plots from plotter ==== #
            # Only make directory if user wants a particular type of plot
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
            if 'SEPARATION' in self.makeplots:
                separationdir = f'{self.dumpdir}/plots/{tree}/Separation'
                self.tree_to_dir[tree]['separationdir'] = separationdir
                os.makedirs(separationdir, exist_ok=True)
            if 'EFF' in self.makeplots:
                effdir = f'{self.dumpdir}/plots/{tree}/Efficiency'
                self.tree_to_dir[tree]['effdir'] = effdir
                os.makedirs(effdir, exist_ok=True)
            if 'PIECHART' in self.makeplots:
                piechartdir = f'{self.dumpdir}/plots/{tree}/PieChart'
                self.tree_to_dir[tree]['piechartdir'] = piechartdir
                os.makedirs(piechartdir, exist_ok=True)
            if '2D' in self.makeplots:
                plot2ddir = f'{self.dumpdir}/plots/{tree}/2D'
                self.tree_to_dir[tree]['heatdir'] = plot2ddir
                os.makedirs(plot2ddir, exist_ok=True)

            # ==== Create the directories to store tables from plotter ==== #
            tablesdir = f'{self.dumpdir}/tables/{tree}'
            self.tree_to_dir[tree]['tablesdir'] = tablesdir
            os.makedirs(tablesdir, exist_ok=True)