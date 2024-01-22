
from collections import defaultdict
from copy import copy, deepcopy
import os, re
import numpy as np
import logging
log = logging.getLogger(__name__)

from plot.PlotClasses import PlotterSettings, CoffeaPlot, Stack, Stackatino, RatioPlot, RatioItem, DataOverMC, Significance, Blinder, PieStack
from util.utils import compute_total_separation
from containers.variables import Eff

def sort_samples(histograms, samples_list, PlotSettings, rebin = None):

    region, rescale, variable = PlotSettings.region, PlotSettings.rescale, PlotSettings.variable
    region_targets_names = region.targets
    variable_label = variable.label
    # ============== Declare categories ============== #
    category_to_samples = defaultdict(list)
    backgrounds, signals, region_targets = [], [], []
    data = None
    refMC = None

    # ============== Loop over subsamples ============== #
    for sample in samples_list:

        # =========== Categorise MC according to config =========== #
        if sample.type != 'DATA':

            category_histogram = histograms[(variable.name, sample.name, region.name, rescale.name)]
            category_histogram.label = variable_label
            category_histogram.color = sample.color
            category_histogram.stylish_sample = sample.label
            category_histogram.stylish_region = region.label
            category_histogram.stylish_rescale = rescale.label

            if rebin is not None:
                category_histogram.rebin(rebin)

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
            if rebin is not None:
                region_target_histogram.rebin(rebin)
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
            if rebin is not None:
                refMC.rebin(rebin)

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
            if rebin is not None:
                bkg.rebin(rebin)
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
            if rebin is not None:
                sig.rebin(rebin)

            signals.append(sig)

        # ============== Data ============== #
        elif sample.type == 'DATA':
            log.debug(f"Setting sample {sample.name} as data")
            # ======= Support one Data sample ====== #
            data = histograms[(variable.name, sample.name, region.name, rescale.name)]
            data.label = variable_label
            data.stylish_sample = sample.label
            data.stylish_region = region.label
            data.stylish_rescale = rescale.label
            if rebin is not None:
                data.rebin(rebin)
        else:
            log.error("Sample type not recognised", sample.type)

    # ============== Check if data sample exists ============== #
    if data is None:
        data =  histograms[(variable.name, 'total', region.name, rescale.name)]
        data.label = variable_label
        data.stylish_sample = 'Data (MC)'
        data.stylish_region = region.label
        data.stylish_rescale = rescale.label
        if rebin is not None:
            data.rebin(rebin)
    PlotSettings.data_histo = data

    # ============== Backgrounds Histo ============== #
    if backgrounds != []:
        tot_backgrounds_histogram = sum(backgrounds)
    else:
        tot_backgrounds_histogram = deepcopy(data)
        values = np.full_like(tot_backgrounds_histogram.values(), 1e-6)
        variances = np.full_like(tot_backgrounds_histogram.values(), 1e-8)
        tot_backgrounds_histogram.h[...] = np.stack([values, variances], axis=-1)


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
        tot_signals_histogram = deepcopy(data)
        values    = np.full_like(tot_signals_histogram.values(), 1e-6)
        variances = np.full_like(tot_signals_histogram.values(), 1e-8)
        tot_signals_histogram.h[...] = np.stack([values, variances], axis=-1)

    tot_signals_histogram.sample = 'signal'
    tot_signals_histogram.label = variable_label
    tot_signals_histogram.stylish_sample = 'Signal'
    tot_signals_histogram.stylish_region = region.label
    tot_signals_histogram.stylish_rescale = rescale.label

    PlotSettings.signals_histos = signals
    PlotSettings.tot_signals_histo = tot_signals_histogram

    # ============== Total Histo ============== #
    total_histogram =  histograms[(variable.name, 'total', region.name, rescale.name)]
    if rebin is not None:
        total_histogram.rebin(rebin)
    total_histogram.label = variable_label
    total_histogram.stylish_sample = 'Total'
    total_histogram.stylish_region = region.label
    total_histogram.stylish_rescale = rescale.label

    PlotSettings.total_mc_histo = total_histogram

    # ============== Region Targets ============== #
    PlotSettings.region_targets_histos = region_targets

    # ============== Ref MC ============== #
    PlotSettings.refMC_histo = refMC

    # ============== Category to Sample map ============== #
    PlotSettings.category_to_samples_histos = category_to_samples


def prepare_1d_plots(histograms, tree, CoffeaPlotSettings):


    if not any(variable.dim == 1 for variable in CoffeaPlotSettings.variables_list):
        return

    # ====== Loop over 1D plots ====== #
    plot_settings_list = []

    unpacked_samples = []
    for sample in CoffeaPlotSettings.samples_list:
        if sample.is_super:
            unpacked_samples.extend(sample.subsamples)
        else:
            unpacked_samples.append(sample)


    if all(s.type != 'DATA' for s in unpacked_samples):
        log.warning("No data sample found, using total MC as data")
    if all(s.type != 'SIG' for s in unpacked_samples):
        log.warning("No signal samples found, setting signal histogram to 0")
    if all(not s.ref  for s in unpacked_samples):
        log.warning("No reference MC sample found, expect no MC/MC ratio plot")

    dont_double_count = []
    for variable in CoffeaPlotSettings.variables_list:
        #if variable.tree != tree: continue
        if variable.dim  != 1:    continue

        if variable.name in dont_double_count:  continue

        log.debug(f"Setting up variable {variable.name}")

        for region in CoffeaPlotSettings.regions_list:
            log.debug(f"Setting up region {region.name}")

            for rescale in CoffeaPlotSettings.rescales_list:
                log.debug(f"Setting up rescale {rescale.name}")

                dont_double_count.append(variable.name.replace(':Num', '').replace(':Denom', ''))

                if isinstance(variable, Eff):
                    variable.name = variable.name.replace(':Num', '').replace(':Denom', '')

                PlotSettings = PlotterSettings(variable, region, rescale )

                # Sort samples and save them to PlotSettings
                sort_samples(histograms, unpacked_samples, PlotSettings, variable.rebin)

                # ================================================ #
                # ============== Create the blinding box ============== #
                # ================================================ #
                blinder = Blinder(PlotSettings.tot_signals_histo, PlotSettings.tot_backgrounds_histo, threshold=CoffeaPlotSettings.blinding)

                # ================================================ #
                # ============== Create the MC stack ============== #
                # ================================================ #
                mc_stack              = Stack(stackatinos = [], bar_type = 'stepfilled', error_type = 'stat', plottersettings = PlotSettings)
                log.debug(f"Preparing MC stack")
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
                log.debug(f"Preparing Data stack")
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
                # ============== Create the Separation stack ============== #
                # ================================================ #
                sep_stack              = Stack(stackatinos = [], bar_type = 'step', error_type = 'stat', plottersettings = PlotSettings)
                signals_histograms = PlotSettings.signals_histos
                for signal_histogram in signals_histograms:
                    signal_stackatino = Stackatino([signal_histogram], label = signal_histogram.stylish_sample, color = signal_histogram.color, fill = None, linewidth=3)
                    signal_stackatino.sum_histograms()
                    sep_stack.append(signal_stackatino)

                background_histogram = PlotSettings.tot_backgrounds_histo
                background_stackatino = Stackatino([background_histogram], label = background_histogram.stylish_sample, color = background_histogram.color, fill = None, linewidth=3)
                background_stackatino.sum_histograms()

                sep_stack.append(background_stackatino)
                PlotSettings.sep_stack = sep_stack

                # ================================================ #
                # ============== Create the Efficiency stack ============== #
                # ================================================ #
                if isinstance(variable, Eff):
                    eff_stack              = Stack(stackatinos = [], bar_type = 'points', error_type = 'stat', plottersettings = PlotSettings)
                    # ============== Make a Stackatino for each category ============== #
                    for category, cat_samples_histograms in PlotSettings.category_to_samples_histos.items():
                        log.debug(f"Adding sample category:  {category} to stack")
                        # ============== Create a Stackatino for each category ============== #
                        # Category color is the color of the first sample in the category
                        for cat_sample_histogram in cat_samples_histograms:
                            stackatino = Stackatino(histograms=[cat_sample_histogram], label=cat_sample_histogram.stylish_sample, color=cat_sample_histogram.color)
                            stackatino.sum_histograms(sample=cat_sample_histogram.sample)
                            eff_stack.append(stackatino)

                    PlotSettings.eff_stack = eff_stack

                # ================================================ #
                # ============== Create the Data/MC ratio ============== #
                # ================================================ #
                log.debug(f"Preparing Data/MC ratio")
                data_over_mc_ratio    = RatioPlot(ratio_items = [], bar_type = 'points', error_type = 'stat', plottersettings = PlotSettings)
                data_over_mc_ratioitem = DataOverMC(data_histogram,  PlotSettings.total_mc_histo, label = None, marker = 'o', color = 'black', markersize=12)
                data_over_mc_ratio.append(data_over_mc_ratioitem)
                data_over_mc_ratio.blinder = blinder
                PlotSettings.data_over_mc_ratio = data_over_mc_ratio

                # ================================================ #
                # ============== Create the MC/MC ratio ============== #
                # ================================================ #
                mc_over_mc_ratio      = RatioPlot(ratio_items = [], bar_type = 'step', error_type = 'stat', plottersettings = PlotSettings)
                log.debug(f"Preparing MC/MC ratio")
                if PlotSettings.refMC_histo is not None:
                    for mc_histogram in PlotSettings.backgrounds_histos+PlotSettings.signals_histos:
                        mc_over_mc_ratioitem = RatioItem(mc_histogram, PlotSettings.refMC_histo, label = None, color = mc_histogram.color, linewidth=3)
                        mc_over_mc_ratio.append(mc_over_mc_ratioitem)
                else:
                    mc_over_mc_ratio = None

                PlotSettings.mc_over_mc_ratio = mc_over_mc_ratio

                # ================================================ #
                # ============== Create the Significance Plot ============== #
                # ================================================ #
                log.debug(f"Preparing Significance ratio plots")
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
                # ============== Create the Piechart stack ============== #
                # ================================================ #
                if CoffeaPlotSettings.piechart_plot_settings is not None:
                    pie_stack = PieStack(stackatinos = [], bar_type = 'pie', error_type = 'stat', plottersettings = PlotSettings)
                    for category, cat_samples_histograms in PlotSettings.category_to_samples_histos.items():
                        for cat_sample_histogram in cat_samples_histograms:
                            if cat_sample_histogram.sample not in CoffeaPlotSettings.piechart_plot_settings.samples: continue
                            # ============== Create a Stackatino for each sample ============== #
                            log.debug(f"Adding sample:  {cat_sample_histogram.sample} to Pie")
                            hpie = histograms[(variable.name+':pie', cat_sample_histogram.sample, region.name , rescale.name)]
                            stackatino = Stackatino(histograms=[hpie], label=cat_sample_histogram.stylish_sample, color=cat_sample_histogram.color, facecolor=cat_sample_histogram.color)
                            # Add up all the histograms in the stackatino
                            stackatino.sum_histograms(sample=cat_sample_histogram.sample)
                            # Add the stackatino to the stack
                            pie_stack.append(stackatino)

                    PlotSettings.pie_stack = pie_stack
                # ================================================ #
                #================= Save plot objects in PlotSettings ============== #
                plot_settings_list.append(PlotSettings)

    return plot_settings_list

def prepare_2d_plots(histograms, tree, CoffeaPlotSettings):

    # ====== Loop over 1D plots ====== #
    plot_settings_list = []

    unpacked_samples = []
    for sample in CoffeaPlotSettings.samples_list:
        if sample.is_super:
            unpacked_samples.extend(sample.subsamples)
        else:
            unpacked_samples.append(sample)

    for variable in CoffeaPlotSettings.variables_list:
        #if variable.tree != tree: continue
        if variable.dim  != 2:    continue

        log.debug(f"Setting up variable {variable.name}")

        for region in CoffeaPlotSettings.regions_list:
            log.debug(f"Setting up region {region.name}")

            for rescale in CoffeaPlotSettings.rescales_list:
                log.debug(f"Setting up rescale {rescale.name}")

            for sample in unpacked_samples:
                PlotSettings = PlotterSettings(variable, region, rescale, sample)

                sample_histo = histograms[(variable.name, sample.name, region.name, rescale.name)]

                sample_histo.label = variable.label
                sample_histo.color = sample.color
                sample_histo.stylish_sample = sample.label
                sample_histo.stylish_region = region.label
                sample_histo.stylish_rescale = rescale.label
                if variable.rebin is not None:
                    sample_histo.rebin(variable.rebin)

                # Category color is the color of the first sample in the category
                stackatino = Stackatino(histograms=[sample_histo], label=sample.label, color=sample.color, linewidth=3)
                # Add up all the histograms in the stackatino
                stackatino.sum_histograms()
                # Add the stackatino to the stack
                mc_stack = Stack(stackatinos = [stackatino], bar_type = 'stepfilled', error_type = 'stat', plottersettings = PlotSettings)


                # Append stack to kust of stacks (one per region, rescale, variable)
                PlotSettings.mc_stack = mc_stack
                plot_settings_list.append(PlotSettings)
    return plot_settings_list

def make_datamc(plot, settings, outpath):

    mc_stack = deepcopy(plot.mc_stack)
    data_stack = deepcopy(plot.data_stack)
    data_over_mc_ratio = deepcopy(plot.data_over_mc_ratio)

    stack_with_datamc = CoffeaPlot([mc_stack, data_stack], data_over_mc_ratio, settings)

    log.info(f"Plotting Data v MC plots")
    stack_with_datamc.plot(outpath)

def make_mcmc(plot, settings, outpath):
    mc_stack = deepcopy(plot.mc_stack)
    mc_over_mc_ratio = deepcopy(plot.mc_over_mc_ratio)

    if mc_over_mc_ratio is None:
        mc_over_mc_ratio = []

    mc_stack.stack = False
    mc_stack.bar_type = 'step'

    mcmc_plot = CoffeaPlot(mc_stack, mc_over_mc_ratio, settings)
    log.info(f"Plotting MC v MC plots")
    mcmc_plot.plot(outpath)

def make_eff(plot, settings, outpath):
    if plot.eff_stack is None:
        log.warning("No efficiency stack found")
        return

    eff_stack = deepcopy(plot.eff_stack)
    settings.main.ynorm = False
    eff_plot = CoffeaPlot(eff_stack, [], settings)

    log.info(f"Plotting Efficiency plots")
    eff_plot.plot(outpath)

def make_separation(plot, settings, outpath):
    sep_stack = deepcopy(plot.sep_stack)
    sep_stack.stack = False

    if  settings.writesep:

        signal_stackatinos = sep_stack.stackatinos[:-1]
        signal_h = sum(stackatino.sum.h for stackatino in signal_stackatinos)
        background_stackatino = sep_stack.stackatinos[-1]
        bkg_h = background_stackatino.sum.h

        separation = compute_total_separation(signal_h, bkg_h)
        separation_str = f"Separation: {separation*100:.2f} %"

    sep_plot = CoffeaPlot(sep_stack, [], settings, add_auto_text = [[separation_str, settings.seploc]])
    log.info(f"Plotting Separation plots")
    sep_plot.plot(outpath)

def make_significance(plot, settings, outpath):
    mc_stack = deepcopy(plot.mc_stack)
    data_stack = deepcopy(plot.data_stack)
    signif_ratios = plot.signif_ratios

    stack_with_signif = CoffeaPlot([mc_stack, data_stack], signif_ratios, settings)
    log.info(f"Plotting Significance plots")
    stack_with_signif.plot(outpath)

def make_piechart(plot, settings, outpath):

    if plot.pie_stack is None:
        log.warning("No pie stack found")
        return

    pie_stack = deepcopy(plot.pie_stack)
    piechart = CoffeaPlot([pie_stack], [], settings)
    log.info(f"Plotting Pie Charts")
    piechart.plot(outpath, plot_type='PIE')

def make_heatmap(plot, settings, outpath):
    mc_stack = deepcopy(plot.mc_stack)
    heatmap  = CoffeaPlot([mc_stack], [], settings)
    heatmap.plot(outpath, plot_type='2D')


def make_plots(plot_settings_list, CoffeaPlotSettings, outpaths):
    makeplots = CoffeaPlotSettings.makeplots
    for plot in plot_settings_list:

        log.info(f"Making plots for {plot.variable.name} in {plot.region.name} with {plot.rescale.name} rescale")

        if 'DATAMC' in makeplots:
            outpath = outpaths['datamcdir']
            make_datamc(plot, CoffeaPlotSettings.datamc_plot_settings, outpath)
        if 'MCMC' in makeplots:
            outpath = outpaths['mcmcdir']
            make_mcmc(plot, CoffeaPlotSettings.mcmc_plot_settings, outpath)
        if 'SIGNIF' in makeplots:
            outpath = outpaths['significancedir']
            make_significance(plot, CoffeaPlotSettings.significance_plot_settings, outpath)
        if 'SEPARATION' in makeplots:
            outpath = outpaths['separationdir']
            make_separation(plot, CoffeaPlotSettings.separation_plot_settings, outpath)
        if 'EFF' in makeplots:
            outpath = outpaths['effdir']
            make_eff(plot, CoffeaPlotSettings.eff_plot_settings, outpath)
        if 'PIECHART' in makeplots:
            outpath = outpaths['piechartdir']
            make_piechart(plot, CoffeaPlotSettings.piechart_plot_settings, outpath)

def make_2d_plots(plot_settings_list, CoffeaPlotSettings, outpaths):
    makeplots = CoffeaPlotSettings.makeplots
    if '2D' in makeplots:
        outpath = outpaths['heatdir']
        for plot in plot_settings_list:
            make_heatmap(plot, CoffeaPlotSettings.heatmap_plot_settings, outpath)



