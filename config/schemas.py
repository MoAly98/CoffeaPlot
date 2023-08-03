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

class CanvasSchema(object):

    def __init__(self, canvas_type='GENERAL', plot_type='GENERAL'):
        general_plot_settings_schema = {
            Optional('figuresize',          default = (24, 18)): And([int], lambda x: len(x) == 2),
            Optional('figuretitle',         default = True): Or(str, bool),
            Optional('figuretitlefontsize', default = 20): int,
            Optional('experiment',          default = 'ATLAS'): str,
            Optional('lumi',                default = 140): Or(int, float),
            Optional('com',                 default = 13): Or(int, float),
            Optional('plotstatus',          default = 'Internal'): str,
            Optional('height_ratios',       default = None): And([int]), # Ratio of main to ratio canvas
        }

        if canvas_type == 'MPLUSR':
            # Main and Ratio canvas
            main_axis_schema = AxisSchema('MAIN')
            ratio_axis_schema = AxisSchema('RATIO')
            general_plot_settings_schema.update({
                Optional('main',  default = main_axis_schema.defaults): main_axis_schema.schema,
                Optional('ratio', default = ratio_axis_schema.defaults): ratio_axis_schema.schema,
            })

            if plot_type == 'DATAMC':
                general_plot_settings_schema.update({
                    Optional('data', default = None): str,
                    Optional('mc', default = None): str
                })

            if plot_type == 'MCMC':
                general_plot_settings_schema.update({
                    Optional('refsamples', default = None): str,
                })

        self.schema = general_plot_settings_schema
        self.defaults  = {k.key: k.default for k in self.schema.keys()}

class AxisSchema(object):

    def __init__(self, ax_type='MAIN'):

        axes_schema = {
            # Y-axis
            Optional('ylabel', default = 'Fraction of Events/bin' if ax_type == 'MAIN' else None): str,
            Optional('ylabelfontsize', default = 26): int,
            Optional('ylog',   default = False): bool,
            Optional('yrange', default = None):  And([Use(float)], lambda x: len(x) == 2),
            # X-axis
            Optional('xrange', default = None):  And([Use(float)], lambda x: len(x) == 2),
            Optional('xlog',   default = False): bool,
            Optional('xlabelfontsize', default = 26): int,
            # Legend
            Optional('legendshow',     default = True if ax_type == 'MAIN' else False): bool,
            Optional('legendfontsize', default = 26): int,
            Optional('legendloc',      default = 'upper right'): Or(str, And([Use(float)], lambda x: len(x) == 2)),
            Optional('legendncol',     default = 2): int,
            Optional('legendoutside',  default = False): bool,
        }

        if ax_type == 'MAIN':
            axes_schema.update({
               Optional('ynorm',  default = True):  bool,
            })

        self.schema = axes_schema

        self.defaults  = {k.key: k.default for k in self.schema.keys()}


class SampleSchema(object):

    def __init__(self, sample_type='SAMPLE'):

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

        subsample_schema = {k: v for k, v in sample_schema.items() if k not in ['ntuplesrgxs']}

        if sample_type == 'SUPERSAMPLE':
            sample_schema = {
                                'name': str,
                                'subsamples': [subsample_schema],
                                'ntuplesrgxs': Or(str, [str]),
                                Optional('ntuplesdirs', default = None): [str]
                            }

        self.schema = sample_schema


sample_schema           = SampleSchema('SAMPLE')
supersample_schema      = SampleSchema('SUPERSAMPLE')
plots_schema            = CanvasSchema('GENERAL', 'GENERAL')
plots_with_ratio_schema = CanvasSchema('MPLUSR', 'GENERAL')
datamc_schema           = CanvasSchema('MPLUSR', 'DATAMC')
mcmc_schema             = CanvasSchema('MPLUSR', 'MCMC')

schema = Schema({
                'general':
                    {
                        'dumpdir': str,
                        'trees': Use(string_to_list),
                        Optional('ntuplesdirs',  default = None): Use(string_to_list),
                        Optional('mcweight',     default = None): Or(str, Use(float), Use(functor_input)), # Name of branch, value, or functor args
                        Optional('inputhistos',  default = None):  Use(string_to_list),
                        Optional('blinding',     default = 0): Use(float),
                        Optional('helpers',      default = None): Use(string_to_list),
                        Optional('runprocessor', default = False): bool,
                        Optional('runplotter',   default = False): bool,
                        Optional('makeplots',    default = ['MCMC', 'DATAMC', 'SIGNIF']): And(Use(string_to_list), lambda x: all([y in ['MCMC', 'DATAMC', 'SIGNIF'] for y in x])),
                        Optional('skipnomrescale', default = False): bool,
                        Optional('loglevel',     default = 3): int,
                        Optional('nworkers',     default = 8): int, # 0 is Iterative executor...
                    },

                'variables':
                    {
                        '1d':[{
                                'name': str,
                                'method':  Or(str, Use(functor_input)), # Name of branch, or functor args
                                'binning': Or(And(str, lambda x: len(x.strip().split(',')) == 3), [Use(float)]),
                                Optional('regions', default = ['.*']): Use(string_to_list),
                                Optional('label',   default = None): str,
                                Optional('idxby',   default = 'event'): And(str, lambda x: x in ['event', 'nonevent']),
                                Optional('rebin',   default = None): [Use(float)],
                            }],
                        Optional('2d', default = []): [{}],# Not implemented yet
                    },

                Optional('samples',     default = []):  [sample_schema.schema],
                Optional('supersamples', default = []): [supersample_schema.schema],

                'regions':
                [{
                            'name': str,
                            'selection': Use(functor_input),
                            Optional('label', default = None): str,
                            Optional('targets', default = []): Or(str, [str]),
                }],

                Optional('rescales', default = []):
                [{
                            'name': str,
                            'method': Or(float, Use(functor_input)),
                            Optional('label', default = None): str,
                            Optional('affects', default = []): Or(str, [str]),
                }],

                Optional('plots',        default = plots_schema.defaults):  plots_schema.schema,
                Optional('datamc',       default = datamc_schema.defaults): datamc_schema.schema,
                Optional('mcmc',         default = mcmc_schema.defaults):   mcmc_schema.schema,
                Optional('significance', default = plots_with_ratio_schema.defaults): plots_with_ratio_schema.schema,
                })