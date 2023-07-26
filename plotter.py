
from classes import _DummySample
from PlotClasses import PlotterSettings, CoffeaPlot, Stack, Stackatino, RatioPlot, RatioItem, DataOverMC, Significance, Blinder
import os, re
from collections import defaultdict
from copy import copy, deepcopy

from logger import ColoredLogger as logger
# TODO:: FilterNones function to get only settings that have been specified by user


def sort_samples(histograms, samples_list, PlotSettings, log: logger = None):

    region, rescale, variable = PlotSettings.region, PlotSettings.rescale, PlotSettings.variable
    region_targets_names = region.targets
    variable_label = variable.label
    # ============== Declare categories ============== #
    category_to_samples = defaultdict(list)
    backgrounds, signals, region_targets = [], [], []
    data = None
    refMC = None

    for a_sample in samples_list:

        # ============== Handle SuperSamples ============== #
        if a_sample.is_super:
            subsamples = a_sample.subsamples
        else:
            subsamples = [a_sample]

        # ============== Loop over subsamples ============== #
        for sample in subsamples:

            # =========== Categorise MC according to config =========== #
            if sample.type != 'DATA':
                category_histogram = histograms[(variable.name, sample.name, region.name, rescale.name)]
                category_histogram.label = variable_label
                category_histogram.color = sample.color
                category_histogram.stylish_sample = sample.label
                category_histogram.stylish_region = region.label
                category_histogram.stylish_rescale = rescale.label

                if sample.category is not None:
                    category_to_samples[sample.category].append(category_histogram)
                else:
                    category_to_samples[sample.label].append(category_histogram)

            # ============== Target samples for this region ============== #
            if any(re.match(region_target_name, sample.name) for region_target_name in region_targets_names):
                log.debug(f"Adding sample {sample.name} to region {region.name} targets")
                region_target_histogram = histograms[(variable.name, sample.name, region.name, rescale.name)]
                region_target_histogram.label = variable_label
                region_target_histogram.color = sample.color
                region_target_histogram.stylish_sample = sample.label
                region_target_histogram.stylish_region = region.label
                region_target_histogram.stylish_rescale = rescale.label
                region_targets.append(region_target_histogram)

            # ========== Support one Reference MC sample ========== #
            if sample.ref == True and refMC is None:
                log.debug(f"Setting sample {sample.name} as reference MC")
                refMC = histograms[(variable.name, sample.name, region.name, rescale.name)]
                refMC.label = variable_label
                refMC.color = sample.color
                refMC.stylish_sample = sample.label
                refMC.stylish_region = region.label
                refMC.stylish_rescale = rescale.label
            elif sample.ref == True and refMC is not None:
                log.error("More than one reference MC sample found")

            # ============== Group Backgrounds ============== #
            if sample.type == 'BKG':
                log.debug(f"Adding sample {sample.name} to backgrounds")
                bkg = histograms[(variable.name, sample.name, region.name, rescale.name)]
                bkg.label = variable_label
                bkg.color = sample.color
                bkg.stylish_sample = sample.label
                bkg.stylish_region = region.label
                bkg.stylish_rescale = rescale.label
                backgrounds.append(bkg)

            # ============== Group Signals ============== #
            elif sample.type == 'SIG':
                log.debug(f"Adding sample {sample.name} to signals")
                sig = histograms[(variable.name, sample.name, region.name, rescale.name)]
                sig.label = variable_label
                sig.color = sample.color
                sig.stylish_sample = sample.label
                sig.stylish_region = region.label
                sig.stylish_rescale = rescale.label
                signals.append(sig)

            # ============== Data ============== #
            elif sample.type == 'DATA':
                log.debug(f"Setting sample {sample.name} as data")
                # ======= Support one Data sample ====== #
                if data is None:
                    data = histograms[(variable.name, sample.name, region.name, rescale.name)]
                    data.label = variable_label
                    data.stylish_sample = sample.label
                    data.stylish_region = region.label
                    data.stylish_rescale = rescale.label
                else:   log.error("More than one data sample found")
            else:
                log.error("Sample type not recognised", sample.type)

    # ============== Check if data sample exists ============== #
    if data is None:
        log.warning("No data sample found, using total MC as data")
        data =  histograms[(variable.name, 'total', region.name, rescale.name)]
        data.label = variable_label
        data.stylish_sample = 'Data (MC)'
        data.stylish_region = region.label
        data.stylish_rescale = rescale.label

    PlotSettings.data_histo = data

    # ============== Backgrounds Histo ============== #
    tot_backgrounds_histogram = sum(backgrounds)
    tot_backgrounds_histogram.sample         = 'background'
    tot_backgrounds_histogram.label = variable_label
    tot_backgrounds_histogram.stylish_sample = 'Background'
    tot_backgrounds_histogram.stylish_region = region.label
    tot_backgrounds_histogram.stylish_rescale = rescale.label
    PlotSettings.backgrounds_histos = backgrounds
    PlotSettings.tot_backgrounds_histo = tot_backgrounds_histogram

    # ============== Signal Histo ============== #
    if signals != []:
        tot_signals_histogram = sum(signals)
    else:
        log.warning("No signal samples found, setting signal histogram to 0")
        tot_signals_histogram = deepcopy(tot_backgrounds_histogram)
        tot_signals_histogram *= 0

    tot_signals_histogram.sample = 'signal'
    tot_signals_histogram.label = variable_label
    tot_signals_histogram.stylish_sample = 'Signal'
    tot_signals_histogram.stylish_region = region.label
    tot_signals_histogram.stylish_rescale = rescale.label

    PlotSettings.signals_histos = signals
    PlotSettings.tot_signals_histo = tot_signals_histogram

    # ============== Total Histo ============== #
    total_histogram =  histograms[(variable.name, 'total', region.name, rescale.name)]
    total_histogram.label = variable_label
    total_histogram.stylish_sample = 'Total'
    tot_signals_histogram.stylish_region = region.label
    tot_signals_histogram.stylish_rescale = rescale.label

    PlotSettings.total_mc_histo = total_histogram

    # ============== Region Targets ============== #
    PlotSettings.region_targets_histos = region_targets

    # ============== Ref MC ============== #
    PlotSettings.refMC_histo = refMC

    # ============== Category to Sample map ============== #
    PlotSettings.category_to_samples_histos = category_to_samples


def prepare_1d_plots(histograms, tree, CoffeaPlotSettings, log):

    # ====== Loop over 1D plots ====== #
    plot_settings_list = []
    for region in CoffeaPlotSettings.regions_list:
        log.info(f"Setting up region {region.name}")
        for variable in CoffeaPlotSettings.variables_list:
            #if variable.tree != tree: continue
            if variable.dim  != 1:    continue
            log.info(f"Setting up variable {variable.name}")

            for rescale in CoffeaPlotSettings.rescales_list:
                log.info(f"Setting up rescale {rescale.name}")

                PlotSettings = PlotterSettings(variable, region, rescale )

                # Sort samples and save them to PlotSettings
                sort_samples(histograms, CoffeaPlotSettings.samples_list, PlotSettings, log)
                # ================================================ #
                # ============== Create the blinding box ============== #
                # ================================================ #
                blinder = Blinder(PlotSettings.tot_signals_histo, PlotSettings.tot_backgrounds_histo, threshold=CoffeaPlotSettings.blinding)

                # ================================================ #
                # ============== Create the MC stack ============== #
                # ================================================ #
                mc_stack              = Stack(stackatinos = [], bar_type = 'stepfilled', error_type = 'stat', plottersettings = PlotSettings)
                log.info(f"Preparing MC stack")
                # ============== Make a Stackatino for each category ============== #
                for category, cat_samples_histograms in PlotSettings.category_to_samples_histos.items():
                    log.debug(f"Adding sample category:  {category} to stack")
                    # ============== Create a Stackatino for each category ============== #
                    # Category color is the color of the first sample in the category
                    stackatino = Stackatino(histograms=[], label=category, color=cat_samples_histograms[0].color, linewidth=3)
                    for cat_sample_histogram in cat_samples_histograms:
                        stackatino.append(cat_sample_histogram)
                    # Add up all the histograms in the stackatino
                    stackatino.sum_histograms()
                    # Add the stackatino to the stack
                    mc_stack.append(stackatino)

                # Append stack to kust of stacks (one per region, rescale, variable)
                PlotSettings.mc_stack = mc_stack

                # ================================================ #
                # ============== Create the Data stack ============== #
                # ================================================ #
                log.info(f"Preparing Data stack")
                data_stack = Stack(stackatinos = [], bar_type = 'points', error_type = 'stat', plottersettings = PlotSettings)
                # ============== Data Stack ==============
                data_histogram = PlotSettings.data_histo
                data_stackicino = Stackatino([data_histogram], label = data_histogram.stylish_sample, color = 'black', fill = None, marker='o', markersize=12)
                data_stackicino.sum_histograms()
                data_stack.append(data_stackicino)
                # Apply blinding
                data_stack.blinder = blinder
                PlotSettings.data_stack = data_stack

                # ================================================ #
                # ============== Create the Data/MC ratio ============== #
                # ================================================ #
                log.info(f"Preparing Data/MC ratio")
                data_over_mc_ratio    = RatioPlot(ratio_items = [], bar_type = 'points', error_type = 'stat', plottersettings = PlotSettings)
                data_over_mc_ratioitem = DataOverMC(data_histogram,  PlotSettings.total_mc_histo, label = None, marker = 'o', color = 'black', markersize=12)
                data_over_mc_ratio.append(data_over_mc_ratioitem)
                data_over_mc_ratio.blinder = blinder
                PlotSettings.data_over_mc_ratio = data_over_mc_ratio
                # ================================================ #
                # ============== Create the MC/MC ratio ============== #
                # ================================================ #
                mc_over_mc_ratio      = RatioPlot(ratio_items = [], bar_type = 'step', error_type = 'stat', plottersettings = PlotSettings)
                log.info(f"Preparing MC/MC ratio")
                if PlotSettings.refMC_histo is not None:
                    for mc_histogram in PlotSettings.backgrounds_histos+PlotSettings.signals_histos:
                        mc_over_mc_ratioitem = RatioItem(mc_histogram, refMC, label = None, color = mc_histogram.color, linewidth=3)
                        mc_over_mc_ratio.append(mc_over_mc_ratioitem)
                else:
                    mc_over_mc_ratio = None
                    log.warning("No reference MC sample found, expect no MC/MC ratio plot")

                PlotSettings.mc_over_mc_ratio = mc_over_mc_ratio
                # ================================================ #
                # ============== Create the Significance Plot ============== #
                # ================================================ #
                log.info(f"Preparing Significance ratio plots")
                signif_ratios_for_one_stack = []
                # ============== Set up significance ratio plots ============== #
                for target_histogram in PlotSettings.region_targets_histos:
                    signif_ratio = RatioPlot(ratio_items = [], bar_type = 'stepfilled', error_type = 'stat', ylabel=f'{target_histogram.sample}/'+r'$\sqrt{B}$', plottersettings = PlotSettings)
                    # Backgrounds to this target (AllMC - Target)
                    background_to_this_target_histograms = [histogram for histogram in PlotSettings.backgrounds_histos+PlotSettings.signals_histos if histogram.sample != target_histogram.sample]
                    background_to_this_target_histogram = sum(background_to_this_target_histograms)
                    background_to_this_target_histogram.sample         = f'background_to_{target_histogram.sample}'
                    background_to_this_target_histogram.stylish_sample = 'Background'

                    # Create a Ratio Item.
                    signif_ratioitem = Significance(target_histogram, background_to_this_target_histogram, color = target_histogram.color, alpha = 0.8)
                    signif_ratio.append(signif_ratioitem)
                    signif_ratios_for_one_stack.append(signif_ratio)

                PlotSettings.signif_ratios = signif_ratios_for_one_stack

                # ================================================ #
                #================= Save plot objects in PlotSettings ============== #
                plot_settings_list.append(PlotSettings)

    return plot_settings_list


# # ====== How many plots to make? ====== #
# num_plots = len(mc_stacks) # x2 for data_over_mc and Significance

# # ======= Now we make 4 CoffeaPlots per region, rescaling, variable ======= #
# # 1. Stack with Data/MC
# # 2. Stack with significance
# # 3. Non-stack with MC/MC (Normalised or Not depending on config)
# # 4. Separation Plots

def make_datamc(plot, settings, outpath):

    mc_stack = deepcopy(plot.mc_stack)
    data_stack = deepcopy(plot.data_stack)
    data_over_mc_ratio = deepcopy(plot.data_over_mc_ratio)

    stack_with_datamc = CoffeaPlot([mc_stack, data_stack], data_over_mc_ratio, settings)
    stack_with_datamc.plot(outpath)


def make_mcmc(plot, settings, outpath):
    mc_stack = deepcopy(plot.mc_stack)
    mc_over_mc_ratio = deepcopy(plot.mc_over_mc_ratio)

    if mc_over_mc_ratio is None:
        mc_over_mc_ratio = []

    mc_stack.stack = False
    mc_stack.bar_type = 'step'

    mcmc_plot = CoffeaPlot(mc_stack, mc_over_mc_ratio, settings)
    mcmc_plot.plot(outpath)

def make_significance(plot, settings, outpath):
    mc_stack = deepcopy(plot.mc_stack)
    data_stack = deepcopy(plot.data_stack)
    signif_ratios = plot.signif_ratios

    stack_with_signif = CoffeaPlot([mc_stack, data_stack], signif_ratios, settings)
    stack_with_signif.plot(outpath)


def make_plots(plot_settings_list, CoffeaPlotSettings, outpaths, log):
    makeplots = CoffeaPlotSettings.makeplots
    for plot in plot_settings_list:

        if 'DATAMC' in makeplots:
            outpath = outpaths['datamcdir']
            make_datamc(plot, CoffeaPlotSettings.datamc_plot_settings, outpath)
        if 'MCMC' in makeplots:
            outpath = outpaths['mcmcdir']
            make_mcmc(plot, CoffeaPlotSettings.mcmc_plot_settings, outpath)
        if 'SIGNIF' in makeplots:
            outpath = outpaths['significancedir']
            make_significance(plot, CoffeaPlotSettings.significance_plot_settings, outpath)


    # # ====== Loop over stacks ========= #
    # for plot_idx in range(plot_settings_list):
    #     mc_stack = mc_stacks[plot_idx]
    #     data_stack = data_stacks[plot_idx]
    #     data_over_mc_ratio = data_over_mc_ratios[plot_idx]
    #     signif_ratio = signif_ratios[plot_idx]

    #     if len(mc_over_mc_ratios) > 0:
    #         mc_over_mc_ratio = mc_over_mc_ratios[plot_idx]

    #     relevant_combo = mc_stack.combo

    #     stack_data_over_mc_settings = {
    #         'figure_size': (24, 18),
    #         'figure_title': f"Region = {relevant_combo.region} & Rescale = {relevant_combo.rescale}",
    #         'experiment': 'ATLAS',
    #         'lumi': 139,
    #         'com': 13,
    #         'plot_status': 'Internal',
    #         'outfile': f"{plot_dir}/data_over_mc/{relevant_combo.variable}__{relevant_combo.region}_{relevant_combo.rescale}.pdf",
    #         'ratio_yrange': (0.5, 1.5),
    #         'ratio_ylabel': 'Data/MC',
    #         'ratio_ylog': False,
    #         'main_yrange': None,
    #         'main_ylog': True,
    #         'main_ylabel': 'Number of Events',
    #     }

    #     stack_with_datamc = CoffeaPlot([mc_stack, data_stack], data_over_mc_ratio, **stack_data_over_mc_settings)
    #     stack_with_datamc.plot()

    #     stack_signif_settings = {
    #         'figure_size': (24, 18),
    #         'figure_title': f"Region = {relevant_combo.region} & Rescale = {relevant_combo.rescale}",
    #         'experiment': 'ATLAS',
    #         'lumi': 139,
    #         'com': 13,
    #         'plot_status': 'Internal',
    #         'outfile': f"{plot_dir}/Significance/{relevant_combo.variable}__{relevant_combo.region}_{relevant_combo.rescale}.pdf",
    #         'ratio_yrange': None,
    #         'ratio_ylabel': None,
    #         'ratio_ylog': False,
    #         'main_yrange': None,
    #         'main_ylog': True,
    #         'main_ylabel': 'Number of Events',
    #     }

    #     stack_with_signif = CoffeaPlot([mc_stack, data_stack], signif_ratio, **stack_signif_settings)
    #     stack_with_signif.plot()

    #     # mcmc_settings = {
    #     #     'figure_size': (24, 18),
    #     #     'figure_title': f"Region = {relevant_combo.region} & Rescale = {relevant_combo.rescale}",
    #     #     'experiment': 'ATLAS',
    #     #     'lumi': 139,
    #     #     'com': 13,
    #     #     'plot_status': 'Internal',
    #     #     'outfile': f"{plot_dir}/MC_v_MC/{relevant_combo.variable}__{relevant_combo.region}_{relevant_combo.rescale}.pdf",
    #     #     'main_yrange': None,
    #     #     'main_ylog': None,
    #     #     'main_ylabel': 'Fraction of Total Events/bin',
    #     #     'main_ynorm': True,
    #     #     'ratio_ylabel': 'Alt/Ref'
    #     # }

    #     mcmc_settings = {
    #         'figure_size': (24, 18),
    #         'figure_title': f"Region = {relevant_combo.region} & Rescale = {relevant_combo.rescale}",
    #         'experiment': 'ATLAS',
    #         'lumi': 139,
    #         'com': 13,
    #         'plot_status': 'Internal',
    #         'outfile': f"{plot_dir}/MC_v_MC/{relevant_combo.variable}__{relevant_combo.region}_{relevant_combo.rescale}.pdf",
    #         'main_yrange': None,
    #         'main_ylog': None,
    #         'main_ylabel': 'Fraction of Total Events/bin',
    #         'main_ynorm': True,
    #         'ratio_ylabel': 'Alt/Ref',
    #         'ratio_yrange': (0, 2),
    #     }


    #     mcmc_stack = deepcopy(mc_stack)
    #     mcmc_stack.stack = False
    #     mcmc_stack.bar_type = 'step'
    #     mcmc_plot = CoffeaPlot(mcmc_stack, mc_over_mc_ratio, **mcmc_settings)
    #     mcmc_plot.plot()