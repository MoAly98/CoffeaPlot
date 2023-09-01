# ================ CoffeaPlot Imports ================ #
import logging
log = logging.getLogger(__name__)
# ================ CoffeaPlot Imports ================ #
from config.plot_classes import (DataMCSettings, MCMCSettings,
                                SeparationSettings,
                                MainPanelSettings, PanelSettings,
                                GeneralPlotSettings as GPS)

def filter_none_settings(settings):
    """
    Remove from settings dictionary all the keys with None value

    Parameters
    ----------
    settings : dict
        Dictionary with settings

    Returns
    -------
    filtered : dict
        Dictionary with settings without None values
    """
    filtered = {}
    for key, value in settings.items():
        if value is not None:
            filtered[key] = value
    return filtered

def parse_general_plot_settings(general_plots_cfg):
    """
    Parse settings that apply to all plots, but can be overwritten by
    speicalised plot settings for the various plots.

    Parameters
    ----------
    general_plots_cfg : dict
        Dictionary with general plot settings, already containing sensible defaults from schema

    Returns
    -------
    GeneralPlotSettings : GPS
        GeneralPlotSettings object with all the settings saved as attributes
    """
    GeneralPlotSettings = GPS()

    for key, value in general_plots_cfg.items():
        setattr(GeneralPlotSettings, key, value)

    return GeneralPlotSettings

def parse_panel_settings(panel_cfg,  panel_type):
    """
    Parse settings for a panel on plot

    Parameters
    ----------
    panel_cfg : dict
        Dictionary with panel settings, already containing sensible defaults from schema
    panel_type : str
        Type of panel, either 'MAIN' or 'RATIO'

    Returns
    -------
    AxisSettings : AxisSettings
        AxisSettings object with all the settings saved as attributes

    """
    if panel_type   == 'MAIN':
        AxisSettings = MainPanelSettings()
    else:
        AxisSettings = PanelSettings()

    for key, value in panel_cfg.items():
        setattr(AxisSettings, key, value)

    return AxisSettings

def parse_special_plot_settings(cfg, plot_type, GeneralPlotSettings):
    """
    Parse settings for specific plots. Supported plots are: 'MCMC', 'DATAMC', 'SIGNIF"

    Parameters
    ----------
    cfg : dict
        Dictionary with all the settings for the plot, with sensible defaults from schema
    plot_type : str
        Type of plot, either 'MCMC', 'DATAMC', 'SIGNIF'
    GeneralPlotSettings : GPS
        GeneralPlotSettings object with all the general plot settings that can be overwritten

    Returns
    -------
    PlotSettings : PlotSettings
        PlotSettings object with all the settings saved as attributes and defaults from GeneralPlotSettings
    """

    # Filter out unset settings so that we use defaults from GeneralPlotSettings for them
    filtered_settings = filter_none_settings(cfg)

    # Set the general plot settings as a base
    for key, value in GeneralPlotSettings.__dict__.items():
        filtered_settings[key] = value

    # Parse the panel settings
    filtered_settings['main']   = parse_panel_settings(filtered_settings['main'],  'MAIN')
    filtered_settings['ratio']  = parse_panel_settings(filtered_settings['ratio'], 'RATIO')

    # Prepare class to hold the individual plot settings
    if plot_type   == 'MCMC':
        PlotSettings = MCMCSettings()

    elif plot_type == 'DATAMC':
        PlotSettings = DataMCSettings()

    elif plot_type == 'SEPARATION':
        PlotSettings = SeparationSettings()

    else:
        PlotSettings = PlotWithRatioSettings()

    # Set the individual plot settings, overwriting the general plot settings
    # for settings that are set by user (not None)
    for key, value in filtered_settings.items():
        setattr(PlotSettings, key, value)

    if plot_type == 'SEPARATION':
        if PlotSettings.main.ynorm:
            log.warning('Setting ynorm to False for separation plots, overriding the config')
        PlotSettings.main.ynorm = True

    return PlotSettings