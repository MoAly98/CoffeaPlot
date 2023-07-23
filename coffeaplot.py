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

# Import coffeaplot packages
from config_reader import process as process_config
from logger import ColoredLogger as logger
from processor import CoffeaPlotProcessor
from general_config_parsers import parse_general, parse_samples, parse_regions, parse_variables, parse_rescales

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

    log.info(f"Logging level set to {loglevel}")


def main():

    cfgp = 'config.yaml'
    # Prepare logger
    log = logger()
    log.info("Parsing and Validating config file")
    validated = process_config(cfgp)

    # Update logging level
    setup_logging(log, validated['general']['loglevel'])

    # =========== Set up general settings =========== #
    CoffeaPlotSettings = parse_general(validated['general'], log)
    CoffeaPlotSettings.setup_inputpaths()
    CoffeaPlotSettings.setup_outpaths()
    CoffeaPlotSettings.setup_helpers()

    # =========== Set up samples, regions, variables, and rescales =========== #
    all_samples_cfg = validated['samples'] + validated['supersamples']
    parse_samples(all_samples_cfg, CoffeaPlotSettings, log)
    parse_regions(validated['regions'], CoffeaPlotSettings, log)
    parse_variables(validated['variables'], CoffeaPlotSettings, log)
    parse_rescales(validated['rescales'], CoffeaPlotSettings, log)

    total_histograms =  (CoffeaPlotSettings.NumSamples
                        *len(CoffeaPlotSettings.regions_list)
                        *len(CoffeaPlotSettings.rescales_list)
                        *len(CoffeaPlotSettings.variables_list)
                        *len(CoffeaPlotSettings.trees) + # plus Total histograms
                        len(CoffeaPlotSettings.regions_list)
                        *len(CoffeaPlotSettings.rescales_list)
                        *len(CoffeaPlotSettings.variables_list))

    log.info(f"Ready to process {total_histograms} histograms")
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
            with open(f"{datadir}/data___{tree}.pkl", "rb") as f:
                out = pickle.load(f)

        # ====== Loop over 1D plots ====== #
        pprint(out)
        print(out[('new_bdt_tH', 'ttlight', 'SR', 'Nominal')].values())







if __name__ == '__main__':
    main()



