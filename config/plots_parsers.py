import logging
log = logging.getLogger(__name__)

from config.classes import DataMCSettings, MCMCSettings, SignificanceSettings, MainCanvasSettings, RatioCanvasSettings, CanvasSettings, GeneralPlotSettings as GPS

def filter_none_settings(settings):
    filtered = {}
    for key, value in settings.items():
        if value is not None:
            filtered[key] = value
    return filtered

def choose_priority_opt(opt_name, priority, secondary):
    if priority[opt_name] is not None:
        return priority[opt_name]
    else:
        return secondary[opt_name]

def parse_general_plots(general_plots_cfg):
    GeneralPlotSettings = GPS()
    #if general_plots_cfg is None:   return None
    for key, value in general_plots_cfg.items():
        setattr(GeneralPlotSettings, key, value)

    # GeneralPlotSettings.figure_size = general_plots_cfg['figuresize']
    # GeneralPlotSettings.plot_title = general_plots_cfg['figuretitle']
    # GeneralPlotSettings.lumi = general_plots_cfg['lumi']
    # GeneralPlotSettings.energy = general_plots_cfg['energy']
    # GeneralPlotSettings.experiment = general_plots_cfg['experiment']
    # GeneralPlotSettings.plot_status = general_plots_cfg['plotstatus']
    # GeneralPlotSettings.height_ratios = general_plots_cfg['heightratios']
    return GeneralPlotSettings

def parse_axis(axis_cfg,  canvas_type):

    if canvas_type == 'MAIN':
        AxisSettings = MainCanvasSettings()
    elif canvas_type == 'RATIO':
        AxisSettings = RatioCanvasSettings()
    else:
        AxisSettings = CanvasSettings()

    for key, value in axis_cfg.items():
        setattr(AxisSettings, key, value)

    # AxisSettings.ylabel          = axis_cfg['ylabel']
    # AxisSettings.ylog            = axis_cfg['ylog']
    # AxisSettings.yrange          = axis_cfg['yrange']
    # AxisSettings.ylabelfontsize  = axis_cfg['ylabelfontsize']
    # AxisSettings.xrange          = axis_cfg['xrange']
    # AxisSettings.xlabelfontsize  = axis_cfg['xlabelfontsize']
    # AxisSettings.legend_show     = axis_cfg['legendshow']
    # AxisSettings.legend_loc      = axis_cfg['legendloc']
    # AxisSettings.legend_ncol     = axis_cfg['legendncol']
    # AxisSettings.legend_fontsize = axis_cfg['legendfontsize']
    # AxisSettings.legend_outside  = axis_cfg['legendoutside']

    return AxisSettings

def parse_settings(cfg, settings_class, GeneralPlotSettings):

    filtered_settings = filter_none_settings(cfg)

    for key, value in GeneralPlotSettings.__dict__.items():
        filtered_settings[key] = value


    filtered_settings['main'] = parse_axis(filtered_settings['main'], 'MAIN') #MainCanvasSettings(parse_axis())
    filtered_settings['ratio'] = parse_axis(filtered_settings['ratio'], 'RATIO')
    # for key, value in filtered_settings.items():
    #     if key == 'main':
    #         MainAxisSettings = MainCanvasSettings(parse_axis(value))
    #         value = MainAxisSettings
    #     if key == 'ratio':
    #         RatioAxisSettings = RatioCanvasSettings(parse_axis(value))
    #         filtered_settings['main'] = RatioAxisSettings


    if settings_class   == 'MCMC':
        PlotSettings = MCMCSettings()
    elif settings_class == 'SIGNIF':
        PlotSettings = SignificanceSettings()
    elif settings_class == 'DATAMC':
        PlotSettings = DataMCSettings()

    for key, value in filtered_settings.items():
        setattr(PlotSettings, key, value)

    # if cfg['main'] is None:
    #     MainAxisSettings = None
    # else:
    #     MainAxisSettings = MainCanvasSettings(parse_axis(cfg['main']))
    #     MainAxisSettings.ynorm = cfg['main']['ynorm']

    # if cfg['ratio'] is None:
    #     RatioAxisSettings = None
    # else:
    #     RatioAxisSettings = RatioCanvasSettings(parse_axis(cfg['ratio']))





    # filtered_settings = filter_none_settings(cfg)
    # if 'main' in filtered_settings: del filtered_settings['main']
    # if 'ratio' in filtered_settings: del filtered_settings['ratio']

    # for key, value in GeneralPlotSettings.__dict__.items():
    #     filtered_settings[key] = value



    # PlotSettings.figure_size  = choose_priority_opt('figuresize',  cfg, GeneralPlotSettings)
    # PlotSettings.plot_title   = choose_priority_opt('figuretitle', cfg, GeneralPlotSettings)
    # PlotSettings.lumi         = choose_priority_opt('lumi',        cfg, GeneralPlotSettings)
    # PlotSettings.energy       = choose_priority_opt('com',         cfg, GeneralPlotSettings)
    # PlotSettings.experiment   = choose_priority_opt('experiment',  cfg, GeneralPlotSettings)
    # PlotSettings.plot_status  = choose_priority_opt('plotstatus',  cfg, GeneralPlotSettings)
    # PlotSettings.height_ratios= choose_priority_opt('height_ratios', cfg, GeneralPlotSettings)

    return PlotSettings

# def parse_datamc(datamc_cfg, GeneralPlotSettings):
#     DataMCPlotSettings = parse_settings(datamc_cfg, 'DATAMC', GeneralPlotSettings)
#     #DataMCPlotSettings.data = datamc_cfg['data']
#     #DataMCPlotSettings.mc = datamc_cfg['mc']

#     return DataMCPlotSettings

# def parse_mcmc(mcmc_cfg, GeneralPlotSettings):

#     MCMCPlotSettings = parse_settings(mcmc_cfg, 'MCMC', GeneralPlotSettings)
#     #MCMCPlotSettings.refsamples = mcmc_cfg['refsamples']

#     return MCMCPlotSettings

# def parse_significance(significance_cfg, GeneralPlotSettings):

#     SignificancePlotSettings = parse_settings(significance_cfg, 'SIGNIF', GeneralPlotSettings)

#     return SignificancePlotSettings