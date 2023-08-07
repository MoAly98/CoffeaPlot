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
    return validated