import yaml
from schema import Schema, And, Use, Optional, Or
from pprint import pprint

def functor_input(inlist):

    if len(inlist) != 2:
        raise SchemaError("Expecting a list of length 2 here")
    if not isinstance(inlist[0], str):
        raise SchemaError("Expecting a string here")

    second_element = string_to_list(inlist[1])
    return [inlist[0], second_element]

def string_to_list(value):
    if not isinstance(value, str) and not isinstance(value, list):
        raise SchemaError("Expecting a string or list of strings here")
    if isinstance(value, str):
        return [value]
    return value


def keys_to_lower(mydict):
    newdict = {}
    for k in mydict.keys():
        if isinstance(mydict[k], dict):
            newdict[k.lower()] = keys_to_lower(mydict[k])
        else:
            if isinstance(mydict[k], list):
                newdict[k.lower()] = [keys_to_lower(i) if isinstance(i, dict) else i for i in mydict[k]]
            else:
                newdict[k.lower()] = mydict[k]
    return newdict

def validate(indict):
    mydict = keys_to_lower(indict)
    the_schema = Schema({
                        'general':
                            {
                                'dumpdir': str,
                                'trees': Use(string_to_list),
                                Optional('ntuplesdirs'. default = None): Use(string_to_list),
                                Optional('mcweight', default = None): Or(str, Use(float), Use(functor_input)), # Name of branch, value, or functor args
                                Optional('inputhistos', default = None): str,
                                Optional('helpers', default = None): Use(string_to_list),
                                Optional('runprocessor', default = False): bool,
                                Optional('runplotter',   default = False): bool,
                                Optional('skipnomrescale', default = False): bool,
                                Optional('loglevel', default = 3): int,
                                Optional('nworkers', default = 8): int, # 0 is Iterative executor...
                            },
                        'variables':
                            {
                                '1d':
                                    [
                                        {
                                            'name': str,
                                            'method':  Or(str, Use(functor_input)), # Name of branch, or functor args
                                            'binning': Or(And(str, lambda x: len(x.strip().split(',') == 3)), [Use(float)]),
                                            Optional('label', default = None): str,
                                        }
                                    ],
                                Optional('2D', default = None): [{}],# Not implemented yet
                            },
                        'samples':
                            [
                                {#[str, Or(str, [str])]
                                    'name': str,
                                    'type': And(str, lambda s: s in ['SIG', 'BKG', 'DATA']),
                                    'ntuplesrgxs': Or(str, [str]),
                                    Optional('selection', default = None): Use(functor_input),
                                    Optional('ntuplesdirs', default = None): [str],
                                    Optional('weight', default = None): Or(str, Use(float), Use(functor_input)),
                                    Optional('ignoremcweight', default = False): bool,
                                    Optional('refmc', default = False): bool,
                                    Optional('label', default = None): str,
                                    Optional('color', default = None): str,
                                    Optional('category', default = None): str,

                                }
                            ],

                        'regions':
                            [
                                {
                                    'name': str,
                                    'selection': Use(functor_input),
                                    Optional('label', default = None): str,
                                    Optional('targets', default = None): Or(str, [str]),
                                }
                            ],

                        Optional('rescales', default = None):
                            [
                                {
                                    'name': str,
                                    'method': Or(float, Use(functor_input)),
                                    Optional('label', default = None): str,
                                    Optional('affects', default = None): Or(str, [str]),
                                }
                            ],


                        })

    validated =  the_schema.validate(mydict)
    return validated

def process(cfgp):
    with open(f'config.yaml','r') as f:
        output = yaml.safe_load(f)
        validated = validate(output)

    return validated
