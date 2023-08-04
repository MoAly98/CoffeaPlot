import logging
log = logging.getLogger(__name__)

from config.classes import (DataMCSettings, MCMCSettings,
                            MainCanvasSettings, CanvasSettings,
                            GeneralPlotSettings as GPS)

def filter_none_settings(settings):
    filtered = {}
    for key, value in settings.items():
        if value is not None:
            filtered[key] = value
    return filtered

def parse_general_plot_settings(general_plots_cfg):
    GeneralPlotSettings = GPS()

    for key, value in general_plots_cfg.items():
        setattr(GeneralPlotSettings, key, value)

    return GeneralPlotSettings

def parse_axis_settings(axis_cfg,  canvas_type):

    if canvas_type   == 'MAIN':
        AxisSettings = MainCanvasSettings()
    else:
        AxisSettings = CanvasSettings()

    for key, value in axis_cfg.items():
        setattr(AxisSettings, key, value)

    return AxisSettings

def parse_special_plot_settings(cfg, plot_type, GeneralPlotSettings):

    filtered_settings = filter_none_settings(cfg)

    for key, value in GeneralPlotSettings.__dict__.items():
        filtered_settings[key] = value


    filtered_settings['main'] = parse_axis_settings(filtered_settings['main'], 'MAIN')
    filtered_settings['ratio'] = parse_axis_settings(filtered_settings['ratio'], 'RATIO')

    if plot_type   == 'MCMC':
        PlotSettings = MCMCSettings()

    elif plot_type == 'DATAMC':
        PlotSettings = DataMCSettings()

    else:
        PlotSettings = PlotWithRatioSettings()

    for key, value in filtered_settings.items():
        setattr(PlotSettings, key, value)


    return PlotSettings