import yaml
from config_schema import schema
from pprint import pprint
from utils import keys_to_lower

def validate(indict):
    mydict = keys_to_lower(indict)
    validated =  schema.validate(mydict)
    return validated

def process(cfgp):
    with open(cfgp,'r') as f:
        output = yaml.safe_load(f)
        validated = validate(output)

    return validated