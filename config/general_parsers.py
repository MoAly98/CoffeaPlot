# ======= Pythonic Imports ======= #
import numpy as np
import logging
log = logging.getLogger(__name__)
# ======= CoffeaPlot Imports ======= #
from containers.samples import Sample, SuperSample
from containers.regions import Region
from containers.rescales import Rescale
from containers.variables import Variable, Variables, Eff
from containers.functors import Functor
from config.general_classes import CoffeaPlotSettings as CPS


def same_name_obj_found(obj_name, alist):
    """
    Check if an object with the same name as obj_name is found in alist.
    Special handling for cases where an object is searched for in a list
    with Supersample objects, where the subsamples should be searched.

    Parameters
    ----------
    obj_name : str
        Name of object to search for
    alist : list
        List of objects to search in

    Returns
    -------
    found : bool
        True if object with same name is found in alist, False otherwise
    """
    names_list = []
    for elem in alist:
        if isinstance(elem, SuperSample):
            names_list.extend([ss.name for ss in elem.subsamples])
        else:
            names_list.append(elem.name)

    return any([obj_name == name_in_list for name_in_list in names_list])


def create_weights_functor(weight, CoffeaPlotSettings, sample_name):
    """
    Create a functor instance to define weights to apply to events. This uses
    the weight configuration from the config file, and the functions defined
    in the helper modules.

    Parameters
    ----------
    weight : str, float, list
        The weight configuration from the config file
    CoffeaPlotSettings : CPS object
        The CoffeaPlotSettings object containing the helper functions
    sample_name : str
        The name of the sample to be used in logging

    Returns
    -------
    weight_functor : Functor
        The functor instance to be used to define weights in processor
    """

    # =========== If user provided weight confiuration that is a list, they expect to use a function =========== #
    if isinstance(weight, list):
        # The function used in config file mut be defined in a helper module
        if CoffeaPlotSettings.functions is None:
            log.error(f"Function {weight[0]} is not defined in any helper module. Please check your configuration file.")

        # Create a functor instance to be used to define weights
        weight_fn = CoffeaPlotSettings.functions[weight[0]]
        weight_functor = Functor(weight_fn, weight[1])
        log.debug(f"Sample {sample_name} weight set to use function {weight_functor.fn.__repr__()} with arguments {weight[1]}")

    # ======== If user provided weight configuration that is a string, they expect to use a branch ======== #
    elif isinstance(weight, str):
        # Create a functor instance to be used to define weights as just the branch
        weight_functor = Functor(lambda w: w, [weight])
        log.debug(f"Sample {sample_name} weight set to use branch {weight}")

    # ======== If user provided weight configuration that is a float, they expect to use a constant weighting ======== #
    else:
        # Create a functor instance to be used to define weights as a constant rescaling
        weight_functor = Functor(lambda w: w*weight, ['weights'])
        log.debug(f"Sample {sample_name} weight set to use float {weight}")

    return weight_functor


def parse_general(general_cfg: dict,):
    """
    Parse the general settings from the configuration file.

    Parameters
    ----------
    general_cfg : dict
        The dictionary containing the general settings from the configuration

    Returns
    -------
    CoffeaPlotSettings : CPS object
    """

    log.info(f"Setting up general settings")
    Settings = CPS()

    # Set up the helper functions first so that they can be used in parsing
    # the rest of the configuration
    Settings.helpers      = general_cfg['helpers']
    Settings.setup_helpers()

    # Set up the MC weight functors to be used in the processor
    mc_weight_functor = create_weights_functor(general_cfg['mcweight'], Settings, 'All MC')
    Settings.mcweight = mc_weight_functor
    log.info(f"Using the following function for MC weights: {mc_weight_functor.fn.__repr__()}")

    # Set up rest of general settings that don't need special handling
    for key, value in general_cfg.items():

        # Skip the mcweight and helpers keys since they were already handled
        if key in ['mcweight', 'helpers']: continue

        # Set the attribute in the CoffeaPlotSettings object
        setattr(Settings, key, value)

        log.debug(f"The following general setting was parsed:")
        log.debug(f"{key} = {value}")

    return Settings

def parse_samples(samples_cfg: dict, CoffeaPlotSettings: CPS):
    """
    Parse the samples settings from the configuration file.

    The method will loop over samples (or subsamples in case of SuperSamples)
    and will handle the various settings before using them to create a Sample
    instance. Various checks will be done to ensure the settings are valid.

    All samples parsed are saved into a list that is saved in the CoffeaPlotSettings
    instance passed as an argument.


    Parameters
    ----------
    samples_cfg : dict
        The dictionary containing the samples settings from the configuration

    CoffeaPlotSettings : CPS
        The CoffeaPlotSettings object containing the general settings

    Returns
    -------
    None
    """

    log.info(f"Setting up samples ...")

    # Declarations needed for parsing
    samples_list = []
    num_samples = 0
    data_sample_found = False

    for sample in samples_cfg:
        # ============= Handle super samples ============= #
        is_supersample = False
        if 'subsamples' in sample:
            subsamples = sample['subsamples']
            # Create a SuperSample instance
            supersample = SuperSample(sample['name'])
            is_supersample = True
        else:
            subsamples = [sample]

        for subsample in subsamples:
            sample_name = subsample['name']
            log.info(f"Setting up sample {sample_name}")


            # ======= Check sample type is valid ======= #
            sample_type =  subsample['type'].upper()
            if sample_type not in ['BKG','SIG','DATA', 'GHOST']:
                log.error(f"Sample {sample_name} has unknown type {sample_type}. Please check your configuration file.")

            if sample_type == 'GHOST':
                raise NotImplementedError("GHOST samples are not yet implemented")

            # ======= Check that only one data sample is given ======= #
            sample_is_data = sample_type.upper() == 'DATA'
            if data_sample_found and sample_is_data:
                log.error(f"More than one data sample found. Please check your configuration file.")
            if sample_is_data:  data_sample_found = True

            # ===== Check that MC reference sample is not a data sample ===== #
            sample_is_mc_ref = subsample['refmc']
            if sample_is_mc_ref and sample_is_data:
                log.error(f"Sample {sample_name} is marked as reference MC but is of type data. This is not allowed.")

            # ============ Check n-tuples dir is available for this sample ============ #
            get_dirs_from = CoffeaPlotSettings

            # Deal with standalone samples first
            if not is_supersample:
                # If an ntuples directory is given for this sample, use it
                if subsample['ntuplesdirs'] is not None:
                    get_dirs_from = subsample
                # If no ntuples directory is given for this sample, and none is given in general settings, break
                elif subsample['ntuplesdirs'] is  None and CoffeaPlotSettings.ntuplesdirs is None:
                    log.error(f"No ntuples directory given for sample {sample_name} and none given in general settings.")
                else:
                    # Directory is given in general settings, use it
                    pass
            # Now deal with supersamples
            else:
                # If an ntuples directory is given for this subsample, use it
                if subsample['ntuplesdirs'] is not None :
                    get_dirs_from = subsample

                # If ntuples directory is not given for this subsample, try to get it from the supersample
                elif subsample['ntuplesdirs'] is None and sample['ntuplesdirs'] is not None:
                    get_dirs_from = sample

                # If no ntuples directory is given for this subsample, and none is given in the supersample and none is given in general settings, break
                elif subsample['ntuplesdirs'] is None and sample['ntuplesdirs'] is None and CoffeaPlotSettings.ntuplesdirs is None:
                    log.error(f"No ntuples directory given for sample {sample_name} and none given in general settings or supersample.")

                else:
                    # Directory is given in general settings, use it
                    pass

            # Get the ntuples directory to use
            look_in = get_dirs_from['ntuplesdirs']
            log.debug(f"Using ntuples directory {look_in} for sample {sample_name}")


            # ======= Prepare functor for sample selector ======= #
            selection = subsample['selection']
            selection_functor = None
            if selection is not None:
                selection_fn      = CoffeaPlotSettings.functions.get(selection[0], None)
                if selection_fn is None:
                    log.error(f"Function {selection[0]} is not defined in any helper module. Please check your configuration file.")
                selection_functor = Functor(selection_fn, selection[1])
                log.debug(f"Sample selector set to use function {selection[0]} with arguments {selection[1]}")
            else:
                log.debug(f"Sample {sample_name} has no special selection.")

            # ======= Prepare functor for sample weight ======= #
            weight =  subsample['weight']
            weight_functor = create_weights_functor(weight, CoffeaPlotSettings, sample_name)

            # Handle MC weight usage for this  sample
            sample_ignore_mcweight = subsample['ignoremcweight']
            # If sample is data, set mc weight to 1
            if sample_is_data:
                mc_weight_functor = create_weights_functor(1., CoffeaPlotSettings, sample_name)

            # If user specifies to ignore mc weight, set it to 1
            elif sample_ignore_mcweight:
                mc_weight_functor = create_weights_functor(1., CoffeaPlotSettings, sample_name)

            # Otherwise, use the mc weight from general settings
            else:
                mc_weight_functor = CoffeaPlotSettings.mcweight

            log.debug(f"Sample {sample_name} will use the following weight: {mc_weight_functor.fn.__repr__()} * {weight_functor.fn.__repr__()}")

            #  ====== Get the regexes to use for this sample ====== #
            # For a subsample of a supersample, use the regexes given in the supersample
            if is_supersample:  get_rgx_from = sample
            else:   get_rgx_from = subsample
            sample_regexes = get_rgx_from['ntuplesrgxs']
            log.info(f"Using the following regexes for sample {sample_name}: {sample_regexes}")

            # ======= Create sample object ======= #
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


            # ========= check for unique sample names ========= #
            # Check if sample is defined more than once
            if same_name_obj_found(sample_obj.name, samples_list):
                log.error(f"Sample {sample_name} is defined more than once. Please check your configuration file.")


            # ========== Handle how we store super-samples ========== #
            if is_supersample:
                # Add subsample to supersample
                supersample.add_subsample(sample_obj)
                # Set regex and directories to use for this supersample
                supersample.regexes = sample_regexes
                supersample.direcs = look_in
                continue

            # Create fileset for sample to be passed to processor, if processor is to be run
            if CoffeaPlotSettings.runprocessor:
                sample_obj.create_fileset()

            # Add sample to list of samples
            samples_list.append(sample_obj)

            # Count sample for logging
            num_samples += 1

        if is_supersample:
            if CoffeaPlotSettings.runprocessor:
                supersample.create_fileset()
            samples_list.append(supersample)
            num_samples += len(supersample)



    # Set the list of samples and the number of samples in the settings object
    CoffeaPlotSettings.samples_list = samples_list
    CoffeaPlotSettings.NumSamples = num_samples

    log.info(f"Created {num_samples} samples")


def parse_regions(regions_cfg: dict, CoffeaPlotSettings: CPS):
    '''
    Parse the regions settings from the configuration file.

    This method loops over the regions defined in the configuration file
    and will handle the various settings before using them to create a
    Region object for each region.

    All regions parsed are saved into a list that is saved in the CoffeaPlotSettings
    instance passed as an argument.

    Parameters
    ----------
    regions_cfg : dict
        The regions settings from the configuration file.

    CoffeaPlotSettings : CPS
        The CoffeaPlotSettings instance to save the regions list to.

    Returns
    -------
    None
    '''
    log.info("Parsing regions....")
    regions_list = []
    for region in regions_cfg:

        # ========= check for unique region names ========= #
        region_name = region['name']
        if same_name_obj_found(region_name, regions_list):
            log.error(f"Region {region_name} is defined more than once. Please check your configuration file.")

        # ========= set up region selection ========= #
        selection = region['selection']
        selection_fn = CoffeaPlotSettings.functions[selection[0]]
        selection_functor = Functor(selection_fn, selection[1])

        # ========= Create Region instance and pass it to list ========= #
        regions_list.append(Region(name = region_name,
                                   howto = selection_functor,
                                   target_sample = region['targets'],
                                   label = region['label']))

    log.info(f"Created {len(regions_list)} regions")
    CoffeaPlotSettings.regions_list = regions_list


def parse_variables(variables_cfg, CoffeaPlotSettings):

    """
    Parse the variables settings from the configuration file.

    This method loops over the variables defined in the configuration file
    and will handle the various settings before using them to create a
    Variable object for each variable.

    All variables parsed are saved into a list that is saved in the CoffeaPlotSettings
    instance passed as an argument.

    Parameters
    ----------
    variables_cfg : dict
        The variables settings from the configuration file.

    CoffeaPlotSettings : CPS
        The CoffeaPlotSettings instance to save the variables list to.

    Returns
    -------
    None
    """

    variables_list = []

    # Loop over 1D variables
    for variable in variables_cfg['1d']+variables_cfg['2d']:

        # ====== Check for unique variable names ====== #
        variable_name = variable['name']
        if same_name_obj_found(variable_name, variables_list):
            log.error(f"Variable {variable_name} is defined more than once. Please check your configuration file.")


        # ====== Set up the method for creating the variable ====== #
        # Method can be a functor or a branch name
        if 'methodx' in variable and 'methody' in variable:
            howto = [variable['methodx']] + [variable['methody']]
            howto_functor = []
            for axis_method in howto:
                if isinstance(axis_method, list):
                    # Method is a functor
                    method_fn = CoffeaPlotSettings.functions[axis_method[0]]
                    func = Functor(method_fn, axis_method[1])
                else:
                    # Method is simply a branch name
                    func = Functor(lambda x: x, [axis_method])

                howto_functor.append(func)
        else:
            howto = variable['method']
            if isinstance(howto, list):
                # Method is a functor
                method_fn = CoffeaPlotSettings.functions[howto[0]]
                howto_functor = Functor(method_fn, howto[1])
            else:
                # Method is simply a branch name
                howto_functor = Functor(lambda x: x, [howto])

        # ====== Set up the binning for the variable histogram ====== #
        # Binning can be a list of bin edges or a list with [min, max, nbins]
        if isinstance(variable['binning'], str):
            minbin, maxbin, nbins = variable['binning'].strip().split(',')
            binning = np.linspace(float(minbin), float(maxbin), int(nbins))
        else:
            binning = variable['binning']


        # ====== Create Variable instance and pass it to list ====== #

        if variable.get('numsel', None) is  None:
            variables_list.append(Variable(name = variable_name,
                                            howto = howto_functor,
                                            binning = binning,
                                            label = variable['label'],
                                            regions = variable['regions'],
                                            idx_by = variable['idxby'],
                                            dim = len(howto_functor),
                                            rebin = variable['rebin']))
        else:
            # This is only possible for 1D plots by schema implementation
            numsel = variable['numsel']
            if isinstance(numsel, list):
                # Method is a functor
                method_fn = CoffeaPlotSettings.functions[numsel[0]]
                numsel_functor = Functor(method_fn, numsel[1])
            else:
                # Method is simply a branch name
                numsel_functor = Functor(lambda x: x, [numsel])

            denomsel = variable['denomsel']
            if isinstance(denomsel, list):
                # Method is a functor
                method_fn = CoffeaPlotSettings.functions[denomsel[0]]
                denomsel_functor = Functor(method_fn, denomsel[1])
            else:
                # Method is simply a branch name
                denomsel_functor = Functor(lambda x: x, [denomsel])

            # Enter with 2 histograms
            variables_list.append(Eff(name = variable_name+":Num",
                                      howto = howto_functor,
                                      binning = binning,
                                      numsel = numsel_functor,
                                      denomsel = denomsel_functor,
                                      label = variable['label'],
                                      regions = variable['regions'],
                                      idx_by = variable['idxby'],
                                      dim = 1,
                                      rebin = variable['rebin']))

            variables_list.append(Eff(name = variable_name+":Denom",
                                      howto = howto_functor,
                                      binning = binning,
                                      numsel = numsel_functor,
                                      denomsel = denomsel_functor,
                                      label = variable['label'],
                                      regions = variable['regions'],
                                      idx_by = variable['idxby'],
                                      dim = 1,
                                      rebin = variable['rebin']))

    # Loop over 2D variables
    for variable in variables_cfg['2d']:
        continue

    log.info(f"Created {len(variables_list)} variables")
    CoffeaPlotSettings.variables_list = variables_list

def parse_rescales(rescales_cfg, CoffeaPlotSettings):
    """
    Parse the rescales settings from the configuration file.

    This method loops over the rescales defined in the configuration file
    and will handle the various settings before using them to create a
    Rescale object for each rescale.

    All rescales parsed are saved into a list that is saved in the CoffeaPlotSettings
    instance passed as an argument.

    Parameters
    ----------
    rescales_cfg : dict
        The rescales settings from the configuration file.

    CoffeaPlotSettings : CPS
        The CoffeaPlotSettings instance to save the rescales list to.

    Returns
    -------
    None
    """

    rescales_list = []
    for rescale in rescales_cfg:

        # ====== Check for unique rescale names ====== #
        rescale_name = rescale['name']
        if same_name_obj_found(rescale_name, rescales_list):
            log.error(f"Rescale {rescale_name} is defined more than once. Please check your configuration file.")

        # ====== Set up the method for creating the rescale ====== #
        # Method can be a functor or a constant rescale by float
        howto = rescale['method']
        if isinstance(howto, list):
            # Method is a functor
            howto_functor = Functor(CoffeaPlotSettings.functions[howto[0]], howto[1])
        else:
            # Method is simply a float to apply to weights branch
            howto_functor = Functor(lambda x: x*howto, ['weights'])

        # ====== Create Rescale instance and pass it to list ====== #
        rescales_list.append(Rescale(name = rescale['name'],
                                     affected_samples_names = rescale['affects'],
                                     howto = howto_functor,
                                     label = rescale['label']))

    # ====== Add nominal rescale if not skipped by user ====== #
    if not CoffeaPlotSettings.skipnomrescale:
        rescales_list.append(Rescale(name = 'Nominal',
                                     affected_samples_names = ['.*'],
                                     howto = Functor(lambda w: w, ['weights']),
                                     label = 'Nominal'))

    log.info(f"Created {len(rescales_list)} rescales")
    CoffeaPlotSettings.rescales_list = rescales_list