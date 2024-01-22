from schema import Schema, And, Use, Optional, Or

def functor_input(inlist):
    """
    This method takes a list of length 2, where the first element is a string and the second element is either a string or a list of strings.
    Any string in the second element is converted to a list of length 1. The method returns a list of length 2, where the first element is
    the name of a function and the second element is a list of arguments to the function. These are used to create a functor objects.

    Parameters
    ----------
    inlist : list
        List of length 2, where the first element is a string and the second element is either a string or a list of strings.

    Returns
    -------
    list
        List of length 2, where the first element is the name of a function and the second element is a list of arguments to the function.

    """
    if len(inlist) != 2:
        raise SchemaError("Expecting a list of length 2 here")
    if not isinstance(inlist[0], str):
        raise SchemaError("Expecting a string here")

    second_element = string_to_list(inlist[1])
    return [inlist[0], second_element]

def string_to_list(value):
    """
    This method takes an argument htat is either a string or list. If it is a string,
    it is converted to a list of length 1. If it is a list, it is returned as is.

    Parameters
    ----------
    value : str or list
        Argument that is either a string or list.

    Returns
    -------
    list
        List of length 1 if the argument was a string, otherwise the argument is returned as is.
    """
    if not isinstance(value, str) and not isinstance(value, list):
        raise SchemaError("Expecting a string or list of strings here")
    if isinstance(value, str):
        return [value]
    return value

def text_and_loc(value):
    """
    This method takes an argument that is either a string or list. If it is a string
    then this is the text to be written on canvas, and its location is chosen automatically
    by the code. If it is a list, then first element should be a string, and second should
    be either a string or a list of length 2, both of which are meant to specify the location
    of the text on the canvas.

    Parameters
    ----------
    value : str or list
        Argument that is either a string or list.

    Returns
    -------
    list
        List of length 2, where the first element is the text to be written on canvas, and the second element is the location of the text on the canvas.
    """
    if isinstance(value, str):
        return [value, None]
    elif isinstance(value, list):
        if len(value) != 2:
            raise SchemaError("Expecting a list of length 2 here")
        if not isinstance(value[0], str):
            raise SchemaError("Expecting a string here")
        if not isinstance(value[1], str) and not isinstance(value[1], list):
            raise SchemaError("Expecting a string or list of strings here")
        if isinstance(value[1], list) and len(value[1]) != 2:
            raise SchemaError("Expecting a list of length 2 here")

        return value

class CanvasSchema(object):
    """
    Class to handle the schema for a general canvas. It hold generic canvas
    options and sensible defaults for them.

    Each of the options have corrspinding class attributes in the classes
    GeneralPlotSettings (and its child classes).
    """
    def __init__(self, canvas_type='GENERAL', plot_type='GENERAL'):

        # ========== All plots have the following attributes ========== #
        general_plot_settings_schema = {
            Optional('figuresize',          default = (24, 18)): And([int], lambda x: len(x) == 2),
            Optional('figuretitle',         default = True): Or(str, bool),
            Optional('figuretitlefontsize', default = 20): int,
            Optional('experiment',          default = 'ATLAS'): str,
            Optional('lumi',                default = 140): Or(int, float),
            Optional('energy',              default = 13): Or(int, float),
            Optional('status',              default = 'Internal'): str,
            Optional('heightratios',        default = None): And([int]), # Ratio of main to ratio canvas
        }

        # ========== If non-general canvas (e.g. DATAMC) schema is being built, set defaults to None ========== #
        # This allows later to check if a setting is set for specific plots that
        # should override the general settings
        if canvas_type != 'GENERAL':
            for k, v in general_plot_settings_schema.items():
                k.default = None

        # ========== Canvases with a MAIN+RATIO panels have the following attributes ========== #
        if canvas_type == 'MPLUSR':

            # Get the schema for main and ratio panels
            main_axis_schema = PanelSchema('MAIN', plot_type, axes=True)
            ratio_axis_schema = PanelSchema('RATIO')

            # Add the schema for main and ratio panels to the canvas schema
            general_plot_settings_schema.update({
                Optional('main',  default = main_axis_schema.defaults): main_axis_schema.schema,
                Optional('ratio', default = ratio_axis_schema.defaults): ratio_axis_schema.schema,
            })

            # ======= MPLUSR Canvases displaying data and MC have the following attributes ======= #
            if plot_type == 'DATAMC':
                general_plot_settings_schema.update({
                    Optional('data', default = None): str,
                    Optional('mc',   default = None): str
                })

            # ======= MPLUSR Canvases displaying MC v MC have the following attributes ======= #
            if plot_type == 'MCMC':
                general_plot_settings_schema.update({
                    Optional('refsamples', default = None): str,
                })

            # ======= MPLUSR Canvases displaying separation have the following attributes ======= #
            if plot_type == 'SEPARATION':
                general_plot_settings_schema.update({
                    Optional('writesep', default = True): bool,
                    Optional('seploc', default = 'upper center'): Or(str, [Use(float),Use(float)]),
                })

        if canvas_type == 'GENERAL':
            if plot_type == 'PIECHART':
                main_axis_schema = PanelSchema('MAIN', plot_type, axes=False)
                general_plot_settings_schema.update({
                    'samples': [str],
                    # Default is total MC. If set, samples should be fractions of sumsample adding to 1.
                    Optional('sumsample', default = None): str,
                    Optional('main',  default = main_axis_schema.defaults): main_axis_schema.schema,
                })

        # set the schema and defaults
        self.schema = general_plot_settings_schema
        self.defaults  = {k.key: k.default for k in self.schema.keys() if isinstance(k, Optional)}

class PanelSchema(object):
    """
    This class holds the schema for a single panel. It holds generic panel
    options and sensible defaults for them. Each option will have a corrspinding
    class attribute in the class PanelSettings (and its child classes).
    """
    def __init__(self, panel_type='MAIN', plot_type='GENERAL', axes=True):
        # ===== All panels have the following attributes ===== #
        panels_schema = {
            # Legend
            Optional('legendshow',     default = True if panel_type == 'MAIN' else False): bool,
            Optional('legendfontsize', default = 30): int,
            Optional('legendloc',      default = 'upper right'): Or(str, And([Use(float)], lambda x: len(x) == 2)),
            Optional('legendncol',     default = 2): int,
            Optional('legendoutside',  default = False): bool,
            # Text
            Optional('text', default = [[None, None]]): [Use(text_and_loc)], # ("Hi", (0.1,0.9)) or ("Hi", "upper left")
        }

        if axes:
            panels_schema.update({
                # Y-axis
                Optional('ylabel', default = None): str,
                Optional('ylabelfontsize', default = 30): int,
                Optional('ylog',   default = False): bool,
                Optional('yrange', default = None):  And([Use(float)], lambda x: len(x) == 2),
                # X-axis
                Optional('xrange', default = None):  And([Use(float)], lambda x: len(x) == 2),
                Optional('xlog',   default = False): bool,
                Optional('xlabelfontsize', default = 30): int })

        # ===== Main panels only have the following attributes ===== #
        if panel_type == 'MAIN':
            if plot_type == 'SIGNIF' or plot_type == 'DATAMC':
                ynorm = False
            else:
                ynorm = True
            panels_schema.update({
               Optional('ynorm',  default = ynorm):  bool,
            })

         # set the schema and defaults
        self.schema = panels_schema
        self.defaults  = {k.key: k.default for k in self.schema.keys()}


class SampleSchema(object):
    """
    Class to handle the schema for a sample. It hold generic sample
    options and sensible defaults for them. It also holds the schema for
    subsamples, which are samples that share the same input files but defined
    by different selection. Subsamples are held as attributes of SuperSample objects.
    """
    def __init__(self, sample_type='SAMPLE'):
        # ===== All samples have the following attributes ===== #
        sample_schema = {
                        'name': str,
                        'type': And(str, lambda s: s in ['SIG', 'BKG', 'DATA']),
                        'ntuplesrgxs': Or(str, [str]),
                        Optional('selection', default = None): Use(functor_input),
                        Optional('ntuplesdirs', default = None): [str],
                        Optional('weight', default = 1.): Or(str, Use(float), Use(functor_input)),
                        Optional('ignoremcweight', default = False): bool,
                        Optional('refmc', default = False): bool,
                        Optional('label', default = None): str,
                        Optional('color', default = None): str,
                        Optional('category', default = None): str,
        }

        # ====== subsamples don't need ntuplesrgxs, since these should be defined by the supersample ====== #
        subsample_schema = {k: v for k, v in sample_schema.items() if k not in ['ntuplesrgxs']}

        # ====== Supersamples have the following attributes ====== #
        if sample_type == 'SUPERSAMPLE':
            sample_schema = {
                                'name': str,
                                'subsamples': [subsample_schema],
                                'ntuplesrgxs': Or(str, [str]),
                                Optional('ntuplesdirs', default = None): [str]
                            }

        # set the schema, no need for defaults dict since one cannot get away without defining any samples
        self.schema = sample_schema

class GeneralSettingsSchema(object):
    """
    Class to handle the schema for the general settings. It holds generic
    options and sensible defaults for them.
    """

    def __init__(self):
        general_schema = {
                            'dumpdir': str,
                            'trees': Use(string_to_list),
                            Optional('ntuplesdirs',    default = None): Use(string_to_list),
                            Optional('mcweight',       default = 1.0): Or(str, Use(float), Use(functor_input)), # Name of branch, value, or functor args
                            Optional('inputhistos',    default = None):  Use(string_to_list),
                            Optional('blinding',       default = 0): Use(float),
                            Optional('helpers',        default = None): Use(string_to_list),
                            Optional('runprocessor',   default = False): bool,
                            Optional('runplotter',     default = False): bool,
                            Optional('makeplots',      default = ['MCMC', 'DATAMC', 'SIGNIF', 'SEPARATION', 'EFF', 'PIECHART']): And(Use(string_to_list), lambda x: all([y in ['MCMC', 'DATAMC', 'SIGNIF', 'SEPARATION', 'EFF', 'PIECHART'] for y in x])),
                            Optional('skipnomrescale', default = False): bool,
                            Optional('loglevel',       default = 3): int,
                            Optional('nworkers',       default = 8): int, # 0 is Iterative executor...
                        }

        self.schema = general_schema

class VariableSchema(object):
    """
    Class to handle the schema for a variable. It holds generic
    options and sensible defaults for them. It handles both 1D and 2D variables.
    """
    def __init__(self, dim = 1, result='HIST'):
        if dim == 1:
            variable_schema = {
                                'name': str,
                                'method':  Or(str, Use(functor_input)), # Name of branch, or functor args
                                Optional('binning', default = None): Or(And(str, lambda x: len(x.strip().split(',')) == 3), [Use(float)]),
                                Optional('regions', default = ['.*']): Use(string_to_list),
                                Optional('label',   default = None): str,
                                Optional('idxby',   default = 'event'): And(str, lambda x: x in ['event', 'nonevent']),
                                Optional('rebin',   default = None): [Use(float)],
                            }
            if result == 'EFF':
                variable_schema.update({
                    'numsel':  Or(str, Use(functor_input)), # Name of branch, or functor args
                    'denomsel':  Or(str, Use(functor_input)), # Name of branch, or functor args
                })
        elif dim == 2:
            # Not implemented yet
            variable_schema = {
                                'name': str,
                                'methodx':  Or(str, Use(functor_input)), # Name of branch, or functor args
                                'methody':  Or(str, Use(functor_input)), # Name of branch, or functor args
                                Optional('binning', default = None): And([Or(And(str, lambda x: len(x.strip().split(',')) == 3), [Use(float)])], lambda x: len(x)==2),
                                Optional('regions', default = ['.*']): Use(string_to_list),
                                Optional('label',   default = None): str,
                                Optional('idxby',   default = 'event'): And(str, lambda x: x in ['event', 'nonevent']),
                                Optional('rebin',   default = None): And([[Use(float)]] , lambda x: len(x)==2),
                            }
        else:
            raise NotImplementedError("Histograms can either be 1D or 2D")

        self.schema = variable_schema

class RegionSchema(object):
    """
    Class to handle the schema for a region. It holds generic
    options and sensible defaults for them.
    """
    def __init__(self):
        region_schema = {
                        'name': str,
                        'selection': Use(functor_input),
                        Optional('label',   default = None): str,
                        Optional('targets', default = []): Or(str, [str]),
                    }

        self.schema = region_schema

class RescaleSchema(object):
    """
    Class to handle the schema for a rescale. It holds generic
    options and sensible defaults for them.
    """

    def __init__(self):
        rescale_schema = {
                            'name': str,
                            'method': Or(float, Use(functor_input)),
                            Optional('label', default = None): str,
                            Optional('affects', default = []): Or(str, [str]),
                        }

        self.schema = rescale_schema


# Processing+Plotting
general_schema          = GeneralSettingsSchema()
variable_1d_schema      = VariableSchema(dim=1)
variable_2d_schema      = VariableSchema(dim=2)
eff_schema              = VariableSchema(dim=1, result='EFF')
region_schema           = RegionSchema()
rescale_schema          = RescaleSchema()
sample_schema           = SampleSchema('SAMPLE')
supersample_schema      = SampleSchema('SUPERSAMPLE')

# Plotting Only
plots_schema            = CanvasSchema('GENERAL', 'GENERAL')
plots_with_ratio_schema = CanvasSchema('MPLUSR', 'GENERAL')
datamc_schema           = CanvasSchema('MPLUSR', 'DATAMC')
mcmc_schema             = CanvasSchema('MPLUSR', 'MCMC')
separation_schema       = CanvasSchema('MPLUSR', 'SEPARATION')
piechart_schema         = CanvasSchema('GENERAL', 'PIECHART')

schema = Schema({
                'general': general_schema.schema ,
                'variables': {Optional('1d', default=[]): [variable_1d_schema.schema], Optional('2d', default=[]): [variable_2d_schema.schema]},
                'regions':                              [region_schema.schema],
                Optional('effs',         default = {'1d': [], '2d': []}): {'1d': [eff_schema.schema]},
                Optional('rescales',     default = []): [rescale_schema.schema],
                Optional('samples',      default = []): [sample_schema.schema],
                Optional('supersamples', default = []): [supersample_schema.schema],
                Optional('plots',        default = plots_schema.defaults):  plots_schema.schema,
                Optional('datamc',       default = datamc_schema.defaults): datamc_schema.schema,
                Optional('mcmc',         default = mcmc_schema.defaults):   mcmc_schema.schema,
                Optional('eff',          default = mcmc_schema.defaults):   mcmc_schema.schema,
                Optional('separation',   default = separation_schema.defaults):   separation_schema.schema,
                Optional('significance', default = plots_with_ratio_schema.defaults): plots_with_ratio_schema.schema,
                Optional('piechart',     default = piechart_schema.defaults): piechart_schema.schema,

                })
