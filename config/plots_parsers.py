import logging
log = logging.getLogger(__name__)

from config.classes import DataMCSettings, MCMCSettings, SignificanceSettings, MainCanvasSettings, RatioCanvasSettings, CanvasSettings, GeneralPlotSettings as GPS

def choose_priority_opt(opt_name, priority, secondary):
    if priority[opt_name] is not None:
        return priority[opt_name]
    else:
        return secondary[opt_name]

def parse_general_plots(general_plots_cfg):
    GeneralPlotSettings = GPS()
    if general_plots_cfg is None:   return None
    GeneralPlotSettings.figure_size = general_plots_cfg['figuresize']
    GeneralPlotSettings.plot_title = general_plots_cfg['figuretitle']
    GeneralPlotSettings.lumi = general_plots_cfg['lumi']
    GeneralPlotSettings.energy = general_plots_cfg['com']
    GeneralPlotSettings.experiment = general_plots_cfg['experiment']
    GeneralPlotSettings.plot_status = general_plots_cfg['plotstatus']
    GeneralPlotSettings.height_ratios = general_plots_cfg['height_ratios']
    return GeneralPlotSettings

def parse_axis(axis_cfg):

    AxisSettings = CanvasSettings()
    AxisSettings.ylabel          = axis_cfg['ylabel']
    AxisSettings.ylog            = axis_cfg['ylog']
    AxisSettings.yrange          = axis_cfg['yrange']
    AxisSettings.ylabelfontsize  = axis_cfg['ylabelfontsize']
    AxisSettings.xrange          = axis_cfg['xrange']
    AxisSettings.xlabelfontsize  = axis_cfg['xlabelfontsize']
    AxisSettings.legend_show     = axis_cfg['legendshow']
    AxisSettings.legend_loc      = axis_cfg['legendloc']
    AxisSettings.legend_ncol     = axis_cfg['legendncol']
    AxisSettings.legend_fontsize = axis_cfg['legendfontsize']
    AxisSettings.legend_outside  = axis_cfg['legendoutside']

    return AxisSettings

def parse_settings(cfg, settings_class, GeneralPlotSettings):

    if cfg == {}: return None

    if cfg['main'] is None:
        MainAxisSettings = None
    else:
        MainAxisSettings = MainCanvasSettings(parse_axis(cfg['main']))
        MainAxisSettings.ynorm = cfg['main']['ynorm']

    if cfg['ratio'] is None:
        RatioAxisSettings = None
    else:
        RatioAxisSettings = RatioCanvasSettings(parse_axis(cfg['ratio']))
    if settings_class == 'MCMC':
        PlotSettings = MCMCSettings(MainAxisSettings, RatioAxisSettings)
    elif settings_class == 'SIGNIF':
        PlotSettings = SignificanceSettings(MainAxisSettings, RatioAxisSettings)
    elif settings_class == 'DATAMC':
        PlotSettings = DataMCSettings(MainAxisSettings, RatioAxisSettings)

    PlotSettings.figure_size  = choose_priority_opt('figuresize',  cfg, GeneralPlotSettings)
    PlotSettings.plot_title   = choose_priority_opt('figuretitle', cfg, GeneralPlotSettings)
    PlotSettings.lumi         = choose_priority_opt('lumi',        cfg, GeneralPlotSettings)
    PlotSettings.energy       = choose_priority_opt('com',         cfg, GeneralPlotSettings)
    PlotSettings.experiment   = choose_priority_opt('experiment',  cfg, GeneralPlotSettings)
    PlotSettings.plot_status  = choose_priority_opt('plotstatus',  cfg, GeneralPlotSettings)
    PlotSettings.height_ratios= choose_priority_opt('height_ratios', cfg, GeneralPlotSettings)

    return PlotSettings

def parse_datamc(datamc_cfg, GeneralPlotSettings):
    DataMCPlotSettings = parse_settings(datamc_cfg, 'DATAMC', GeneralPlotSettings)

    DataMCPlotSettings.data = datamc_cfg['data']
    DataMCPlotSettings.mc = datamc_cfg['mc']

    return DataMCPlotSettings

def parse_mcmc(mcmc_cfg, GeneralPlotSettings):

    MCMCPlotSettings = parse_settings(mcmc_cfg, 'MCMC', GeneralPlotSettings)

    MCMCPlotSettings.refsamples = mcmc_cfg['refsamples']

    return MCMCPlotSettings

def parse_significance(significance_cfg, GeneralPlotSettings):

    SignificancePlotSettings = parse_settings(significance_cfg, 'SIGNIF', GeneralPlotSettings)

    return SignificancePlotSettings