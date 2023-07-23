from schema import Schema, And, Use, Optional, Or
from copy import deepcopy


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

sample_schema = {
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

subsample_schema = deepcopy(sample_schema)

del subsample_schema['ntuplesrgxs']

supersample_schema = {
                        'name': str,
                        'subsamples': [subsample_schema],
                        'ntuplesrgxs': Or(str, [str]),
                        Optional('ntuplesdirs', default = None): [str]
                    }

schema = Schema({
                        'general':
                            {
                                'dumpdir': str,
                                'trees': Use(string_to_list),
                                Optional('ntuplesdirs', default = None): Use(string_to_list),
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
                                            'binning': Or(And(str, lambda x: len(x.strip().split(',')) == 3), [Use(float)]),
                                            Optional('regions', default = ['.*']): Use(string_to_list),
                                            Optional('label', default = None): str,
                                            Optional('idxby', default = 'event'): And(str, lambda x: x in ['event', 'nonevent']),
                                        }
                                    ],
                                Optional('2d', default = []): [{}],# Not implemented yet
                            },

                        'samples':  [sample_schema],
                        Optional('supersamples', default = []):[supersample_schema],

                        'regions':
                            [
                                {
                                    'name': str,
                                    'selection': Use(functor_input),
                                    Optional('label', default = None): str,
                                    Optional('targets', default = None): Or(str, [str]),
                                }
                            ],

                        Optional('rescales', default = []):
                            [
                                {
                                    'name': str,
                                    'method': Or(float, Use(functor_input)),
                                    Optional('label', default = None): str,
                                    Optional('affects', default = None): Or(str, [str]),
                                }
                            ],


                        })