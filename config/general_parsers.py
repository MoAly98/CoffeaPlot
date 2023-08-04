import numpy as np

import logging
log = logging.getLogger(__name__)

from containers.samples import Sample, SuperSample
from containers.regions import Region
from containers.rescales import Rescale
from containers.variables import Variable, Variables
from containers.functors import Functor
from config.general_classes import CoffeaPlotSettings as CPS

# ========================================= #
# =========== Helper functions =========== #
# ========================================= #
same_name_obj_found = lambda obj_name, alist: any([obj_name == o.name for o in alist])

def create_weights_functor(weight, CoffeaPlotSettings, sample_name = 'None'):

    # Weight is a functor
    if isinstance(weight, list):
        if CoffeaPlotSettings.functions is None:
            log.error(f"Function {weight[0]} is not defined in any helper module. Please check your configuration file.")

        weight_fn = CoffeaPlotSettings.functions[weight[0]]
        weight_functor = Functor(weight_fn, weight[1])
        log.debug(f"Sample {sample_name} weight set to use function {weight_functor.fn.__repr__()} with arguments {weight[1]}")

    # Weight is a branch name
    elif isinstance(weight, str):
        weight_functor = Functor(lambda w: w, [weight])
        log.debug(f"Sample {sample_name} weight set to use branch {weight}")

    # Weight is a float
    else:
        weight_functor = Functor(lambda w: w*weight, ['weights'])
        log.debug(f"Sample {sample_name} weight set to use float {weight}")

    return weight_functor

# ========================================= #
# =========== Setup parsers     =========== #
# ========================================= #

def parse_general(general_cfg: dict,):
    '''
    Parse the general settings from the configuration file.

    Parameters
    ----------
    general_cfg : dict
        The dictionary containing the general settings from the configuration

    Returns
    -------
    CoffeaPlotSettings : CPS object
    '''

    log.info(f"Setting up general settings")
    # =========== Set up general =========== #
    Settings = CPS()

    Settings.helpers      = general_cfg['helpers']
    Settings.setup_helpers()

    for key, value in general_cfg.items():

        if key == 'helpers': continue

        if key == 'mcweight' and value is not None:
            mc_weight_functor = create_weights_functor(value, Settings, 'MC')
            log.info(f"Using the following function for MC weights: {mc_weight_functor.fn.__repr__()}")
            setattr(Settings, key,mc_weight_functor )
        else:
            setattr(Settings, key, value)

        log.debug(f"The following general setting was parsed:")
        log.debug(f"{key} = {value}")

    return Settings

def parse_samples(samples_cfg: dict, CoffeaPlotSettings: CPS):
    '''
    Parse the samples settings from the configuration file.

    The method prepares functors where necessary to use for applying sample
    selection or computing weights. This method relies on the replacement
    file functions for selection, and possibly for weights if user asks
    for a custom function.

    The method sets up the samples_list attribute of the CoffeaPlotSettings.


    Parameters
    ----------
    samples_cfg : dict
        The dictionary containing the samples settings from the configuration

    CoffeaPlotSettings : CPS
        The CoffeaPlotSettings object containing the general settings

    Returns
    -------
    None
    '''

    # =========== Set up samples =========== #
    log.info(f"Setting up samples ...")
    samples_list = []
    num_samples = 0
    data_sample_found = False

    for sample in samples_cfg:

        # Check if sample is a SuperSample
        is_supersample = False
        if 'subsamples' in sample:
            subsamples = sample['subsamples']
            supersample = SuperSample(sample['name'])
            is_supersample = True
        else:
            subsamples = [sample]

        for subsample in subsamples:

            sample_name = subsample['name']
            log.info(f"Setting up sample {sample_name}")


            # Do sample type checks
            sample_type =  subsample['type'].upper()
            if sample_type not in ['BKG','SIG','DATA', 'GHOST']:
                log.error(f"Sample {sample_name} has unknown type {sample_type}. Please check your configuration file.")

            if sample_type == 'GHOST':
                raise NotImplementedError("GHOST samples are not yet implemented")

            sample_is_data = sample_type.upper() == 'DATA'
            if data_sample_found and sample_is_data:
                log.error(f"More than one data sample found. Please check your configuration file.")

            if sample_is_data:  data_sample_found = True


            # Check some ntuples directory is given:
            if subsample['ntuplesdirs'] is None:
                if CoffeaPlotSettings.ntuplesdirs is None:
                    log.error(f'No ntuples directory given for sample {subsample["name"]} and none given in general settings.')
                else:
                    if is_supersample:
                        get_dirs_from = sample
                    else:
                        get_dirs_from = subsample

                    look_in = get_dirs_from['ntuplesdirs'] if get_dirs_from['ntuplesdirs'] is not None else CoffeaPlotSettings.ntuplesdirs
                    log.debug(f"Using ntuples directory {look_in} for sample {sample_name}")


            # Check sample being used as MC reference correctly
            sample_is_mc_ref = subsample['refmc']
            if sample_is_mc_ref and sample_is_data:
                log.error(f"Sample {sample_name} is marked as reference MC but is of type data. This is not allowed.")


            # Prepare selection functor
            selection = subsample['selection']
            selection_functor = None
            if selection is not None:
                selection_fn = CoffeaPlotSettings.functions[selection[0]]
                selection_functor = Functor(selection_fn, selection[1])
                log.debug(f"Sample selector set to use function {selection[0]} with arguments {selection[1]}")
            else:
                log.debug(f"Sample {sample_name} has no special selection.")

            # Prepare weight functor
            weight =  subsample['weight']
            weight_functor = None
            if weight is not None:
                weight_functor = create_weights_functor(weight, CoffeaPlotSettings, sample_name)
            else:
                log.debug(f"Sample {sample_name} has no special weight.")

            # Check if sample should use MCWeight
            sample_ignore_mcweight = subsample['ignoremcweight']
            if sample_is_data:
                mc_weight_functor = None
            elif sample_ignore_mcweight:
                mc_weight_functor = None
            else:
                mc_weight_functor = CoffeaPlotSettings.mcweight

            if mc_weight_functor is not None and weight_functor is not None:
                log.debug(f"Sample {sample_name} will use MCWeight * {weight_functor.fn.__repr__()}")
            if mc_weight_functor is None and weight_functor is not None:
                log.debug(f"Sample {sample_name} will use only {weight_functor.fn.__repr__()}")
            if mc_weight_functor is not None and weight_functor is None:
                log.debug(f"Sample {sample_name} will use only MCWeight")
            if mc_weight_functor is None and weight_functor is None:
                log.debug(f"Sample {sample_name} will not use any weight. Weight = 1.0")


            sample_regexes = get_dirs_from['ntuplesrgxs']
            log.info(f"Using the following regexes for sample {sample_name}: {sample_regexes}")

            # Create sample object
            sample_obj = Sample(name = sample_name,
                            stype = sample_type,
                            direcs = look_in,
                            regexes = sample_regexes,
                            cut_howto = selection_functor,
                            mc_weight = mc_weight_functor,
                            weight_howto = weight_functor,
                            ignore_mcweight = sample_ignore_mcweight,
                            color = subsample['color'],
                            label = subsample['label'],
                            UseAsRef = sample_is_mc_ref,
                            category = subsample['category']
                        )


            if is_supersample:
                supersample.add_subsample(sample_obj)
                supersample.regexes = sample_regexes
                supersample.direcs = look_in
                sample_obj = supersample

            # Check if sample is defined more than once
            if same_name_obj_found(sample_obj.name, samples_list) and not is_supersample:
                log.error(f"Sample {sample_name} is defined more than once. Please check your configuration file.")
            elif same_name_obj_found(sample_obj.name, samples_list) and is_supersample:
                continue


            sample_obj.create_fileset()
            # Add sample to list
            samples_list.append(sample_obj)


        if is_supersample:
            num_samples += len(sample_obj)
        else:
            num_samples += 1


    CoffeaPlotSettings.samples_list = samples_list

    CoffeaPlotSettings.NumSamples = num_samples

    log.info(f"Created {num_samples} samples")



def parse_regions(regions_cfg: dict, CoffeaPlotSettings: CPS):
    '''
    Parse the regions settings from the configuration file.

    The method prepares functors where necessary to use for applying region

    '''

    # =========== Set up regions =========== #
    regions_list = []
    for region in regions_cfg:

        region_name = region['name']
        if same_name_obj_found(region_name, regions_list):
            log.error(f"Region {region_name} is defined more than once. Please check your configuration file.")

        # Set up selection functor
        selection = region['selection']
        selection_fn = CoffeaPlotSettings.functions[selection[0]]
        selection_functor = Functor(selection_fn, selection[1])

        regions_list.append(Region(name = region_name,
                                   howto = selection_functor,
                                   target_sample = region['targets'],
                                   label = region['label']))

    log.info(f"Created {len(regions_list)} regions")
    CoffeaPlotSettings.regions_list = regions_list


def parse_variables(variables_cfg, CoffeaPlotSettings):

    # =========== Set up variables =========== #
    variables_list = []
    for variable in variables_cfg['1d']:

        variable_name = variable['name']

        # Handle method
        howto = variable['method']

        if isinstance(howto, list):
            # Method is a functor
            method_fn = CoffeaPlotSettings.functions[howto[0]]
            howto_functor = Functor(method_fn, howto[1])
        else:
            # Method is simply a branch name
            howto_functor = Functor(lambda x: x, [howto])

        # Handle binning
        if isinstance(variable['binning'], str):
            minbin, maxbin, nbins = variable['binning'].strip().split(',')
            binning = np.linspace(float(minbin), float(maxbin), int(nbins))
        else:
            binning = variable['binning']


        if same_name_obj_found(variable_name, variables_list):
            log.error(f"Variable {variable_name} is defined more than once. Please check your configuration file.")

        variables_list.append(Variable(name = variable_name,
                                          howto = howto_functor,
                                          binning = binning,
                                          label = variable['label'],
                                          regions = variable['regions'],
                                          idx_by = variable['idxby'],
                                          dim = 1,
                                          rebin = variable['rebin']))

    for variable in variables_cfg['2d']:
        continue

    log.info(f"Created {len(variables_list)} variables")
    CoffeaPlotSettings.variables_list = variables_list

def parse_rescales(rescales_cfg, CoffeaPlotSettings):

    # =========== Set up rescales =========== #
    rescales_list = []

    # Add nominal rescale if not skipped by user
    if not CoffeaPlotSettings.skipnomrescale:
        rescales_list.append(Rescale(name = 'Nominal',
                                     affected_samples_names = ['.*'],
                                     howto = Functor(lambda w: w, ['weights']),
                                     label = 'Nominal'))

    for rescale in rescales_cfg:

        rescale_name = rescale['name']

        # Handle method
        howto = rescale['method']
        if isinstance(howto, list):
            # Method is a functor
            howto_functor = Functor(CoffeaPlotSettings.functions[howto[0]], howto[1])
        else:
            # Method is simply a float
            howto_functor = Functor(lambda x: x*howto, ['weights'])

        if same_name_obj_found(rescale_name, rescales_list):
            log.error(f"Rescale {rescale_name} is defined more than once. Please check your configuration file.")

        rescales_list.append(Rescale(name = rescale['name'],
                                     affected_samples_names = rescale['affects'],
                                     howto = Functor(CoffeaPlotSettings.functions[rescale['method'][0]], rescale['method'][1]),
                                     label = rescale['label']))


    log.info(f"Created {len(rescales_list)} rescales")
    CoffeaPlotSettings.rescales_list = rescales_list