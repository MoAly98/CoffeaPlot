import yaml
from config.schemas import schema
from pprint import pprint
from util.utils import keys_to_lower

def validate(indict):
    mydict = keys_to_lower(indict)
    validated =  schema.validate(mydict)
    return validated

def process(cfgp):
    with open(cfgp,'r') as f:
        output = yaml.safe_load(f)
        validated = validate(output)
        if  validated['samples'] == [] and validated['supersamples'] == []:
            log.error("No samples specified in config file, need at least one sample/supersample !")

    return validated