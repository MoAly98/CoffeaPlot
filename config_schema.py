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



axes_schema = {
                Optional('ylabel', default = None): str,
                Optional('ylabelfontsize', default = 26): int,
                Optional('ylog',   default = False): bool,
                Optional('yrange', default = None):  And([Use(float)], lambda x: len(x) == 2),
                Optional('xrange', default = None):  And([Use(float)], lambda x: len(x) == 2),
                Optional('xlog',   default = False): bool,
                Optional('xlabelfontsize', default = 26): int,
                Optional('legendfontsize', default = 26): int,
                Optional('legendloc', default = 'upper right'): Or(str, And([Use(float)], lambda x: len(x) == 2)),
                Optional('legendncol', default = 2): int,
                Optional('legendoutside', default = False): bool,
                }


main_axis_schema = {
                    **axes_schema,
                    Optional('legendshow', default = True): bool,
                    Optional('ynorm', default = True): bool,
                }

main_axis_defaults = {
                'ylabel': 'Fraction of events / bin',
                'ylabelfontsize': 26,
                'ylog': False,
                'yrange': None,
                'xrange': None,
                'xlog': False,
                'xlabelfontsize': 26,
                'legendfontsize': 26,
                'legendloc': None,
                'legendncol': 2,
                'legendoutside': False,
                'legendshow': True,
                'ynorm': True,
}

ratio_axis_schema = {
                    **axes_schema,
                    Optional('legendshow', default = False): bool,
                }

ratio_axis_defaults = {
                'ylabel': None,
                'ylabelfontsize': 26,
                'ylog': False,
                'yrange': None,
                'xrange': None,
                'xlog': False,
                'xlabelfontsize': 26,
                'legendfontsize': 26,
                'legendloc': None,
                'legendncol': 2,
                'legendoutside': False,
                'legendshow': False,
}

general_plot_settings_schema = {
                                Optional('figuresize', default = (24, 18)): And([int], lambda x: len(x) == 2),
                                Optional('figuretitle', default = True): Or(str, bool),
                                Optional('figuretitlefontsize', default = 20): int,
                                Optional('experiment', default = 'ATLAS'): str,
                                Optional('lumi', default = 140): Or(int, float),
                                Optional('com', default = 13): Or(int, float),
                                Optional('plotstatus', default = 'Internal'): str,
                                Optional('height_ratios', default = None): And([int]), # Ratio of main to ratio canvas
                            }

default_plot_settings= {
                        'figuresize': (24, 18),
                        'figuretitle': True,
                        'figuretitlefontsize':  20,
                        'experiment': 'ATLAS',
                        'lumi':  140,
                        'com': 13,
                        'plotstatus':'Internal',
                        'height_ratios': None,
                    }


plots_with_ratio_schema = {
                            **general_plot_settings_schema,
                            Optional('main', default = main_axis_defaults): main_axis_schema,
                            Optional('ratio', default = ratio_axis_defaults): ratio_axis_schema,
                        }

default_plots_with_ratio = {
                            **default_plot_settings,
                            'main': main_axis_defaults,
                            'ratio': ratio_axis_defaults,
}


datamc_schema = {
                    **plots_with_ratio_schema,
                    Optional('data', default = None): str,
                    Optional('mc', default = None): str
                }

default_datamc = {
                    **default_plots_with_ratio,
                    'data': None,
                    'mc': None
                }

mcmc_schema =   {
                    **plots_with_ratio_schema,
                    Optional('refsamples', default = None): str
                }

default_mcmc = {
                    **default_plots_with_ratio,
                    'refsamples': None
                }


schema = Schema({
                'general':
                    {
                        'dumpdir': str,
                        'trees': Use(string_to_list),
                        Optional('ntuplesdirs', default = None): Use(string_to_list),
                        Optional('mcweight', default = None): Or(str, Use(float), Use(functor_input)), # Name of branch, value, or functor args
                        Optional('inputhistos', default = None):  Use(string_to_list),
                        Optional('blinding', default = 0): Use(float),
                        Optional('helpers', default = None): Use(string_to_list),
                        Optional('runprocessor', default = False): bool,
                        Optional('runplotter',   default = False): bool,
                        Optional('makeplots', default = ['MCMC', 'DATAMC', 'SIGNIF']): And(Use(string_to_list), lambda x: all([y in ['MCMC', 'DATAMC', 'SIGNIF'] for y in x])),
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
                                    Optional('rebin', default = None): [Use(float)],
                                }
                            ],
                        Optional('2d', default = []): [{}],# Not implemented yet
                    },

                Optional('samples', default = []):  [sample_schema],
                Optional('supersamples', default = []): [supersample_schema],

                'regions':
                    [
                        {
                            'name': str,
                            'selection': Use(functor_input),
                            Optional('label', default = None): str,
                            Optional('targets', default = []): Or(str, [str]),
                        }
                    ],

                Optional('rescales', default = []):
                    [
                        {
                            'name': str,
                            'method': Or(float, Use(functor_input)),
                            Optional('label', default = None): str,
                            Optional('affects', default = []): Or(str, [str]),
                        }
                    ],
                Optional('plots', default = default_plot_settings): general_plot_settings_schema,
                Optional('datamc', default = default_datamc): datamc_schema,
                Optional('mcmc', default = default_mcmc): mcmc_schema,
                Optional('significance', default = default_plots_with_ratio): plots_with_ratio_schema,
                })