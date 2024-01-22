'''
This is the steering script for the coffeaplot package. This is the entry
point to all parts of the package, where user specfies various settings via
a configuration file, and then the script takes care of the rest.
'''
# =========== Import statements =========== #
# Import python packages
import os
from coffea import processor
from coffea.nanoevents import  BaseSchema
from pprint import pprint
import cloudpickle as pickle
import argparse
import numpy as np
import logging
from util.logger import ColoredLogger as logger
# Prepare logger
log = logger(name='coffeaplot')

# Import coffeaplot packages
from config.reader import process as process_config
from config.general_parsers import parse_general, parse_samples, parse_regions, parse_variables, parse_rescales
from config.plots_parsers import parse_special_plot_settings, parse_general_plot_settings
from histogram.processor import CoffeaPlotProcessor
from plot.plotter import prepare_1d_plots, make_plots, prepare_2d_plots, make_2d_plots

# ========================================= #
# =========== Set up functions =========== #
# ========================================= #
def setup_logging(loglevel: int):
    '''
    Set up logging for the coffeaplot package. The loglevel is set by the user
    in the configuration file. The loglevel is passed to this function as an
    integer, and then the logging package is set up accordingly.

    Parameters
    ----------
    loglevel : int
        The loglevel set by the user in the configuration file.

    Returns
    -------
    None

    '''
    # =========== Set up LOG =========== #
    if loglevel == 0:
        # ERROR
        log.setLevel(40)
    elif loglevel == 1:
        # WARNING
        logging.root.setLevel(30)
    elif loglevel == 2:
        # INFO
        log.setLevel(20)
    elif loglevel >= 3:
        # DEBUG
        log.setLevel(10)

    log.info(f"Logging level set to {loglevel}, logger name is {log.name}")

def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg",   help="Configuration file to run")
    return parser.parse_args()


def main():

    args = argparser()
    cfgp = args.cfg

    log.info("Parsing and Validating config file")
    validated = process_config(cfgp)

    # Update logging level
    setup_logging(validated['general']['loglevel'])

    # =========== Set up general settings =========== #
    CoffeaPlotSettings = parse_general(validated['general'])
    CoffeaPlotSettings.setup_inputpaths()
    CoffeaPlotSettings.setup_outpaths()
    CoffeaPlotSettings.setup_helpers()

    all_samples_cfg = validated['samples'] + validated['supersamples']
    parse_samples(all_samples_cfg, CoffeaPlotSettings)
    parse_regions(validated['regions'], CoffeaPlotSettings)

    validated['variables']['1d'].extend(validated['effs']['1d'])
    #validated['variables']['2d'].update( validated['effs']['2d'])

    parse_variables(validated['variables'], CoffeaPlotSettings)
    parse_rescales(validated['rescales'], CoffeaPlotSettings)

    total_histograms =  (CoffeaPlotSettings.NumSamples
                        *len(CoffeaPlotSettings.regions_list)
                        *len(CoffeaPlotSettings.rescales_list)
                        *len(CoffeaPlotSettings.variables_list)
                        *len(CoffeaPlotSettings.trees) + # plus Total histograms
                        len(CoffeaPlotSettings.regions_list)
                        *len(CoffeaPlotSettings.rescales_list)
                        *len(CoffeaPlotSettings.variables_list))

    log.info(f"Ready to process {total_histograms} histograms")

    if CoffeaPlotSettings.runplotter:
        # =================== Set up plot settings =================== #
        GeneralPlotSettings      = parse_general_plot_settings(validated['plots'])
        if 'DATAMC' in CoffeaPlotSettings.makeplots:
            CoffeaPlotSettings.datamc_plot_settings       = parse_special_plot_settings(validated['datamc'], 'DATAMC', GeneralPlotSettings)
        if 'MCMC' in CoffeaPlotSettings.makeplots:
            CoffeaPlotSettings.mcmc_plot_settings         = parse_special_plot_settings(validated['mcmc'], 'MCMC', GeneralPlotSettings)
        if 'SIGNIF' in CoffeaPlotSettings.makeplots:
            CoffeaPlotSettings.significance_plot_settings = parse_special_plot_settings(validated['significance'], 'SIGNIF', GeneralPlotSettings)
        if 'SEPARATION' in CoffeaPlotSettings.makeplots:
            CoffeaPlotSettings.separation_plot_settings   = parse_special_plot_settings(validated['separation'], 'SEPARATION', GeneralPlotSettings)
        if 'EFF' in CoffeaPlotSettings.makeplots:
            CoffeaPlotSettings.eff_plot_settings          = parse_special_plot_settings(validated['eff'], 'EFF', GeneralPlotSettings)
        if 'PIECHART' in CoffeaPlotSettings.makeplots:
            CoffeaPlotSettings.piechart_plot_settings     = parse_special_plot_settings(validated['piechart'], 'PIECHART', GeneralPlotSettings)
        if '2D' in CoffeaPlotSettings.makeplots:
            CoffeaPlotSettings.heatmap_plot_settings     = parse_special_plot_settings(validated['histo2d'], '2D', GeneralPlotSettings)

    if not (CoffeaPlotSettings.runplotter or CoffeaPlotSettings.runprocessor):
        log.warning("Setup everything but you are not running plotting or processing ... is that intentional?")
        #return 0
    # =========== Set up fileset =========== #
    fileset = {}
    for sample in CoffeaPlotSettings.samples_list:
        fileset[sample.name] = sample.files

    # =========== Setup executor =========== #
    if CoffeaPlotSettings.nworkers != 0:
        executor = processor.FuturesExecutor(workers=CoffeaPlotSettings.nworkers)
    else:
        executor = processor.IterativeExecutor()

    # =========== Run processor/tree =========== #
    for tree in CoffeaPlotSettings.trees:

        datadir = CoffeaPlotSettings.tree_to_dir[tree]['datadir']
        if CoffeaPlotSettings.runprocessor:
            run = processor.Runner(executor=executor, schema=BaseSchema, skipbadfiles=True)
            out = run(fileset, tree, CoffeaPlotProcessor(CoffeaPlotSettings))

            out = dict(out.to_plot)

            with open(f"{datadir}/data___{tree}.pkl", "wb") as f:
                pickle.dump(out, f)
        else:
            if CoffeaPlotSettings.inputhistos is None:
                with open(f"{datadir}/data___{tree}.pkl", "rb") as f:
                    out = pickle.load(f)

            else:
                out = {}
                for inputhistos_file in CoffeaPlotSettings.inputhistos:
                    with open(inputhistos_file, "rb") as f:
                        out.update(pickle.load(f))

        if CoffeaPlotSettings.runplotter:
            # =========== Set up samples, regions, variables, and rescales =========== #

            plot_settings_list = prepare_1d_plots(out, tree, CoffeaPlotSettings)
            if plot_settings_list is not None:
                make_plots(plot_settings_list, CoffeaPlotSettings, CoffeaPlotSettings.tree_to_dir[tree])

            plot_settings_list = prepare_2d_plots(out, tree, CoffeaPlotSettings)
            if plot_settings_list is not None:
                make_2d_plots(plot_settings_list, CoffeaPlotSettings, CoffeaPlotSettings.tree_to_dir[tree])
if __name__ == '__main__':
    main()



