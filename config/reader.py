# ================ CoffeaPlot Imports ================ #
import logging
log = logging.getLogger(__name__)
from config.schemas import schema
from util.utils import keys_to_lower
# ================ Pythonic Imports ================ #
import yaml

def validate(indict):
    """
    Validate the config file against the schema, and do any further validation

    Parameters
    ----------
    indict : dict
        Dictionary with config file after being read by yaml.safe_load

    Returns
    -------
    validated : dict
        Validated config file as a dictionary
    """
    mydict = keys_to_lower(indict)
    validated =  schema.validate(mydict)
    if  validated['samples'] == [] and validated['supersamples'] == []:
        log.error("No samples specified in config file, need at least one sample/supersample !")

    if 'samples' in validated['piechart']:
        for piechart_sample in validated['piechart']['samples'] + [validated['piechart']['sumsample']]:
            # in case sumsample is not set
            if piechart_sample is None: continue

            bad_piecharts_sample = True

            if any(s['name'] == piechart_sample for s in validated['samples']):
                bad_piecharts_sample = False
            if any(s['name'] == piechart_sample for supersample in validated['supersamples'] for s in supersample['subsamples'] ):
                bad_piecharts_sample = False

            if bad_piecharts_sample:
                log.error(f"Sample {piechart_sample} not found in samples list!")

    if validated['variables']['1d'] == [] and validated['variables']['2d'] == []:
        log.error(f"You must specify either 1D or 2D variables")


    return validated

def process(cfgp):
    """
    Open a config file and validate it against the schema

    Parameters
    ----------
    cfgp : str
        Path to config file

    Returns
    -------
    validated : dict
        Validated config file as a dictionary
    """
    with open(cfgp,'r') as f:
        output = yaml.safe_load(f)
        validated = validate(output)

    exit(1)
    return validated