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

from util.logger import ColoredLogger as logger
# Prepare logger
log = logger(name='coffeaplot')

# Import coffeaplot packages
from config.reader import process as process_config
from config.general_parsers import parse_general, parse_samples, parse_regions, parse_variables, parse_rescales
from config.plots_parsers import parse_special_plot_settings, parse_general_plot_settings
from histogram.processor import CoffeaPlotProcessor
from plot.plotter import prepare_1d_plots, make_plots

# ========================================= #
# =========== Set up functions =========== #
# ========================================= #
def setup_logging(log: logger,loglevel: int):
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
        log.setLevel(30)
    elif loglevel == 2:
        # INFO
        log.setLevel(20)
    elif loglevel == 3:
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
    setup_logging(log, validated['general']['loglevel'])

    # =========== Set up general settings =========== #
    CoffeaPlotSettings = parse_general(validated['general'])
    CoffeaPlotSettings.setup_inputpaths()
    CoffeaPlotSettings.setup_outpaths()
    CoffeaPlotSettings.setup_helpers()

    all_samples_cfg = validated['samples'] + validated['supersamples']
    parse_samples(all_samples_cfg, CoffeaPlotSettings)
    parse_regions(validated['regions'], CoffeaPlotSettings)
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

        # ====== Loop over 1D plots ====== #
        #pprint(out)

        # print("tH, nom", sum(out[('alt_bdt_tH', 'tH', 'SR', 'Nominal')].values()))

        # print("ttlight, PH7", "SR", sum(out[('alt_bdt_tH', 'ttlight_PH7', 'SR', 'Nominal')].values()))
        # print("ttlight, aMCH7", "SR", sum(out[('alt_bdt_tH', 'ttlight_aMCH7', 'SR', 'Nominal')].values()))
        # print("ttlight, pThard1", "SR", sum(out[('alt_bdt_tH', 'ttlight_pThard1', 'SR', 'Nominal')].values()))
        # print("ttlight, AFII", "SR", sum(out[('alt_bdt_tH', 'ttlight_AFII', 'SR', 'Nominal')].values()))

        # print("ttc, PH7", "SR", sum(out[('alt_bdt_tH', 'ttc_PH7', 'SR', 'Nominal')].values()))
        # print("ttc, aMCH7", "SR", sum(out[('alt_bdt_tH', 'ttc_aMCH7', 'SR', 'Nominal')].values()))
        # print("ttc, pThard1", "SR", sum(out[('alt_bdt_tH', 'ttc_pThard1', 'SR', 'Nominal')].values()))
        # print("ttc, AFII", "SR", sum(out[('alt_bdt_tH', 'ttc_AFII', 'SR', 'Nominal')].values()))

        # print("ttb, PH7", "SR", sum(out[('alt_bdt_tH', 'ttb_PH7', 'SR', 'Nominal')].values()))
        # print("ttb, aMCH7", "SR", sum(out[('alt_bdt_tH', 'ttb_aMCH7', 'SR', 'Nominal')].values()))
        # print("ttb, pThard1", "SR", sum(out[('alt_bdt_tH', 'ttb_pThard1', 'SR', 'Nominal')].values()))
        print("ttb, FS", "PR", sum(out[('alt_bdt_tH', 'ttb', 'PR', 'Nominal')].values()))
        print("ttb_5FS_1bB, FS", "PR", sum(out[('alt_bdt_tH', 'ttb_5FS_1bB', 'PR', 'Nominal')].values()))
        print("ttb_5FS_2b, FS", "PR", sum(out[('alt_bdt_tH', 'ttb_5FS_2b', 'PR', 'Nominal')].values()))

        print("ttb, FS", "SR", sum(out[('alt_bdt_tH', 'ttb', 'SR', 'Nominal')].values()))
        print("ttb_5FS_1bB, FS", "SR", sum(out[('alt_bdt_tH', 'ttb_5FS_1bB', 'SR', 'Nominal')].values()))
        print("ttb_5FS_2b, FS", "SR", sum(out[('alt_bdt_tH', 'ttb_5FS_2b', 'SR', 'Nominal')].values()))


        # print("ttlight, PH7", "PR", sum(out[('alt_bdt_tH', 'ttlight_PH7', 'PR', 'Nominal')].values()))
        # print("ttlight, aMCH7", "PR", sum(out[('alt_bdt_tH', 'ttlight_aMCH7', 'PR', 'Nominal')].values()))
        # print("ttlight, pThard1", "PR", sum(out[('alt_bdt_tH', 'ttlight_pThard1', 'PR', 'Nominal')].values()))
        # print("ttlight, AFII", "PR", sum(out[('alt_bdt_tH', 'ttlight_AFII', 'PR', 'Nominal')].values()))

        # print("ttc, PH7", "PR", sum(out[('alt_bdt_tH', 'ttc_PH7', 'PR', 'Nominal')].values()))
        # print("ttc, aMCH7", "PR", sum(out[('alt_bdt_tH', 'ttc_aMCH7', 'PR', 'Nominal')].values()))
        # print("ttc, pThard1", "PR", sum(out[('alt_bdt_tH', 'ttc_pThard1', 'PR', 'Nominal')].values()))
        # print("ttc, AFII", "PR", sum(out[('alt_bdt_tH', 'ttc_AFII', 'PR', 'Nominal')].values()))

        # print("ttb, PH7", "PR", sum(out[('alt_bdt_tH', 'ttb_PH7', 'PR', 'Nominal')].values()))
        # print("ttb, aMCH7", "PR", sum(out[('alt_bdt_tH', 'ttb_aMCH7', 'PR', 'Nominal')].values()))
        # print("ttb, pThard1", "PR", sum(out[('alt_bdt_tH', 'ttb_pThard1', 'PR', 'Nominal')].values()))
        # print("ttb, AFII", "PR", sum(out[('alt_bdt_tH', 'ttb_AFII', 'PR', 'Nominal')].values()))

        # print(out[('new_bdt_tH', 'ttc', 'SR', 'Nominal')].values())
        # print(out[('new_bdt_tH', 'ttb', 'SR', 'Nominal')].values())
        # print(out[('new_bdt_tH', 'tH', 'SR', 'Nominal')].values())
        # print(out[('new_bdt_tH', 'total', 'SR', 'Nominal')].values())
        # print(out[('njets', 'total', 'SR', 'Nominal')].values())

        if CoffeaPlotSettings.runplotter:
            # =========== Set up samples, regions, variables, and rescales =========== #

            plot_settings_list = prepare_1d_plots(out, tree, CoffeaPlotSettings)
            make_plots(plot_settings_list, CoffeaPlotSettings, CoffeaPlotSettings.tree_to_dir[tree])








if __name__ == '__main__':
    main()



