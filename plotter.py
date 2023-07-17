
from classes import *
from  samples import *
from regions import *
from rescalings import *
from variables import *
from utils import *
from plot_utils import *
from PlotClasses import *
from logger import ColoredLogger as logger
import os, re
import pickle
import numpy as np
from collections import defaultdict
from copy import copy, deepcopy

# TODO:: Specify type of sample
# TODO:: Class for Stack and Stackatino (Stack element)
# TODO:: Specify Normalised Signal
# TODO:: Specify fraction of plot used by ratio plot
# TODO:: Specify ratio plot limits
# TODO:: Specify figure size
# TODO:: Specify legend location
# TODO:: Sample categories
# TODO:: Nominal rescale should be added in __init__ using regex for affected samples and processor should use regex match
# TODO:: Other variations of Data/MC ratio plot: DATA - MC, DATA - BKG... (to replace data/mc? or just add more?)
# TODO:: somehow allow user to ask for more customised data/mc plots (e.g. MC subtraction, one specific MC, .. )
# TODO:: User to specify yrange/ylog/ylabel  in config for Significance and DatMC (and any other "ratio" plot added later) -- property of CoffeaPlot
# TODO:: Need to account for allowing multiple ratio plots -- check that for each stack if we have a list of RatioPlot objects...
# TODO:: User config parsing
# TODO:: FilterNones function to get only settings that have been specified by user
# TODO:: NoStack option for doing normal comparison plots
# TODO:: Data/MC multiple ratio panels?

log = logger()
# Stuff user should give me?
dump_to = f"outputs/"

# Stuff i do not need from user
data_dir = f"{dump_to}/data-test/"
log.info(f"Reading plots from {data_dir}")
plot_dir = f"{dump_to}/plots/"
log.info(f"Dumping plots to {plot_dir}")


rescales_list.append(Rescale('ProtNominal', [''], Functor(lambda w: w, ['weights'])))

for (root, _, files) in os.walk(f'{data_dir}', topdown=True):
    for file in files:
        if not file.endswith('.pkl') or "___" not in file:   continue

        tree = file.split('___')[1].split('.')[0]

        with open(f"{data_dir}/{file}", "rb") as f:
            histograms = pickle.load(f)

        # ====== Create directories ====== #
        os.makedirs(f"{plot_dir}/Tables/{tree}/",       exist_ok=True)
        os.makedirs(f"{plot_dir}/Significance/{tree}/", exist_ok=True)
        os.makedirs(f"{plot_dir}/Separation/{tree}/",   exist_ok=True)
        os.makedirs(f"{plot_dir}/data_over_mc/{tree}/", exist_ok=True)
        os.makedirs(f"{plot_dir}/MC_v_MC/{tree}/",      exist_ok=True)


        # ====== Loop over 1D plots ====== #

        stacks = []
        mcmcs = []
        data_stacks = []
        data_over_mc_ratios = []
        mc_over_mc_ratios = []
        signif_ratios = []
        for region in regions_list:
            log.info(f"Setting up region {region.name}")
            region_targets_names = region.targets

            for vars_list in plots_to_make:
                if vars_list.tree != tree: continue
                if vars_list.dim  != 1:    continue
                else:   variables_list = vars_list

            for variable in variables_list:
                log.info(f"Setting up variable {variable.name}")

                variable_label = variable.label

                for rescale in rescales_list:
                    log.info(f"Setting up rescale {rescale.name}")

                    combo_dict = {'region':region.name, 'rescale':rescale.name, 'variable':variable.name}
                    # ============== Create 1x Stack per region, rescaling, variable ============== #
                    stack              = Stack(stackatinos = [], bar_type = 'stepfilled', error_type = 'stat', combo = combo_dict)
                    data_stack         = Stack(stackatinos = [], bar_type = 'points', error_type = 'stat', combo = combo_dict)
                    data_over_mc_ratio = RatioPlot(ratio_items = [], bar_type = 'points', error_type = 'stat', combo = combo_dict)
                    mc_over_mc_ratio   = RatioPlot(ratio_items = [], bar_type = 'step', error_type = 'stat', combo = combo_dict)
                    signif_ratios_for_one_stack = []

                    # ============== Group together samples in different ways ============== #
                    category_to_samples = defaultdict(list)

                    backgrounds = []
                    signals = []
                    region_targets = []
                    data = None
                    refMC = None

                    for sample in samples_list:
                        # ============== Group samples from same category ============== #

                        if sample.type != 'DATA':
                            if sample.category is not None:
                                category_to_samples[sample.category].append(sample)
                            else:
                                category_to_samples[sample.label].append(sample)

                        # ============== Group samples by type ============== #
                        if any(re.match(region_target_name, sample.name) for region_target_name in region_targets_names):
                            log.info(f"Adding sample {sample.name} to region {region.name} targets")
                            region_targets.append(sample)

                        if sample.ref == True:
                            if refMC is None:
                                refMC = sample
                            else:
                                log.error("More than one reference MC sample found")

                        if sample.type == 'BKG':
                            log.info(f"Adding sample {sample.name} to backgrounds")
                            backgrounds.append(sample)


                        elif sample.type == 'SIG':
                            log.info(f"Adding sample {sample.name} to signals")
                            signals.append(sample)

                        elif sample.type == 'DATA':
                            log.info(f"Settiing sample {sample.name} as data")
                            if data is None:
                                data = sample
                            else:
                                log.error("More than one data sample found")
                        else:
                            log.error("Sample type not recognised", sample.type)

                    if data is None:
                        # TODO:: Allow Asimov/CustomAsimov where data is set to MC or customMC
                        log.error("No data sample found")

                    # ============== Total Histo ============== #
                    total_histogram =  histograms[(variable.name, 'total', region.name, rescale.name)]
                    total_histogram.stylish_sample= 'Total'
                    total_histogram.label = variable_label

                    # ============== Backgrounds Histo ============== #
                    backgrounds_histograms = [histograms[(variable.name, background.name, region.name, rescale.name)] for background in backgrounds]
                    tot_backgrounds_histogram = sum(backgrounds_histograms)
                    tot_backgrounds_histogram.sample         = 'background'
                    tot_backgrounds_histogram.stylish_sample = 'Background'
                    tot_backgrounds_histogram.label = variable_label

                    # ============== Signal Histo ============== #
                    signals_histograms = [histograms[(variable.name, signal.name, region.name, rescale.name)] for signal in signals]
                    tot_signals_histogram = sum(signals_histograms)
                    tot_signals_histogram.sample = 'signal'
                    tot_signals_histogram.stylish_sample = 'Signal'
                    tot_signals_histogram.label = variable_label

                    # ============== Data Histo ============== #
                    data_histogram  =  histograms[(variable.name, data.name,  region.name, rescale.name)]
                    data.stylish_sample = sample.label
                    data_histogram.label = variable_label

                    # ============== Data Stack ============== #
                    data_stackicino = Stackatino([data_histogram], label = data.name, color = 'black', fill = None, marker='o', markersize=12)
                    data_stackicino.sum_histograms()
                    data_stack.append(data_stackicino)

                    # ============== Set up a data_over_mc ratio plot ============== #
                    data_over_mc_ratioitem = DataOverMC(data_histogram, total_histogram, label = None, marker = 'o', color = 'black', markersize=12)
                    data_over_mc_ratio.append(data_over_mc_ratioitem)

                    # ============== Set up a mc_over_mc ratio plot ============== #
                    if refMC is not None:
                        refMC_histogram = histograms[(variable.name, refMC.name, region.name, rescale.name)]
                        for sample in backgrounds+signals:
                            altMC_histogram = histograms[(variable.name, sample.name, region.name, rescale.name)]
                            mc_over_mc_ratioitem = RatioItem(altMC_histogram, refMC_histogram, label = None, color = sample.color)
                            mc_over_mc_ratio.append(mc_over_mc_ratioitem)


                    # ============== Set up significance ratio plots ============== #
                    for target in region_targets:

                        signif_ratio = RatioPlot(ratio_items = [], bar_type = 'stepfilled', error_type = 'stat', ylabel=f'{target.name}/'+r'$\sqrt{B}$', combo = combo_dict)

                        # Targer Histogram
                        target_histogram = histograms[(variable.name, target.name, region.name, rescale.name)]

                        # Backgrounds to this target (AllMC - Target)
                        background_to_this_target_histograms = [histograms[(variable.name, sample.name, region.name, rescale.name)] for sample in backgrounds+signals if sample.name != target.name]
                        background_to_this_target_histogram = sum(background_to_this_target_histograms)
                        background_to_this_target_histogram.sample         = f'background_to_{target.name}'
                        background_to_this_target_histogram.stylish_sample = 'Background'
                        background_to_this_target_histogram.label = variable_label

                        # Create a Ratio Item.
                        signif_ratioitem = Significance(target_histogram, background_to_this_target_histogram, color = target.color, alpha = 0.8)
                        signif_ratio.append(signif_ratioitem)
                        signif_ratios_for_one_stack.append(signif_ratio)

                    # ============== Blinding ============== #
                    blinder = Blinder(tot_signals_histogram, tot_backgrounds_histogram, threshold=0.00333)
                    data_stack.blinder = blinder
                    data_over_mc_ratio.blinder = blinder

                    # ============== Make a Stackatino for each category ============== #
                    for category, cat_samples in category_to_samples.items():
                        log.info(f"Setting up category {category}")
                        # Why does new instance reset histograms without setting an arg?
                        stackatino = Stackatino(histograms = [], label = category, color = cat_samples[0].color)
                        for cat_sample in cat_samples:
                            histogram = histograms[(variable.name, cat_sample.name, region.name, rescale.name)]
                            histogram.label = variable_label
                            stackatino.append(histogram)

                        stackatino.sum_histograms()
                        stack.append(stackatino)

                    # ============== Append each Stack to corresponding list of Stacks ============== #
                    stacks.append(stack)
                    data_stacks.append(data_stack)
                    data_over_mc_ratios.append(data_over_mc_ratio)
                    if refMC is not None:
                        mc_over_mc_ratios.append(mc_over_mc_ratio)
                    signif_ratios.append(signif_ratios_for_one_stack)

        # ====== How many plots to make? ====== #
        num_plots = len(stacks) # x2 for data_over_mc and Significance

        # ======= Now we make 4 CoffeaPlots per region, rescaling, variable ======= #
        # 1. Stack with Data/MC
        # 2. Stack with significance
        # 3. Non-stack with MC/MC (Normalised or Not depending on config)
        # 4. Separation Plots

        # ====== Loop over stacks ========= #
        for plot_idx in range(num_plots):
            mc_stack = stacks[plot_idx]
            data_stack = data_stacks[plot_idx]
            data_over_mc_ratio = data_over_mc_ratios[plot_idx]
            signif_ratio = signif_ratios[plot_idx]
            if len(mc_over_mc_ratios) > 0:
                mc_over_mc_ratio = mc_over_mc_ratios[plot_idx]

            relevant_combo = mc_stack.combo

            stack_data_over_mc_settings = {
                'figure_size': (24, 18),
                'figure_title': f"Region = {relevant_combo.region} & Rescale = {relevant_combo.rescale}",
                'experiment': 'ATLAS',
                'lumi': 139,
                'com': 13,
                'plot_status': 'Internal',
                'outfile': f"{plot_dir}/data_over_mc/{relevant_combo.variable}__{relevant_combo.region}_{relevant_combo.rescale}.pdf",
                'ratio_yrange': (0.5, 1.5),
                'ratio_ylabel': 'Data/MC',
                'ratio_ylog': False,
                'main_yrange': None,
                'main_ylog': True,
                'main_ylabel': 'Number of Events',
            }

            stack_with_datamc = CoffeaPlot([mc_stack, data_stack], data_over_mc_ratio, **stack_data_over_mc_settings)
            stack_with_datamc.plot()

            stack_signif_settings = {
                'figure_size': (24, 18),
                'figure_title': f"Region = {relevant_combo.region} & Rescale = {relevant_combo.rescale}",
                'experiment': 'ATLAS',
                'lumi': 139,
                'com': 13,
                'plot_status': 'Internal',
                'outfile': f"{plot_dir}/Significance/{relevant_combo.variable}__{relevant_combo.region}_{relevant_combo.rescale}.pdf",
                'ratio_yrange': None,
                'ratio_ylabel': None,
                'ratio_ylog': False,
                'main_yrange': None,
                'main_ylog': True,
                'main_ylabel': 'Number of Events',
            }

            stack_with_signif = CoffeaPlot([mc_stack, data_stack], signif_ratio, **stack_signif_settings)
            stack_with_signif.plot()

            mcmc_settings = {
                'figure_size': (24, 18),
                'figure_title': f"Region = {relevant_combo.region} & Rescale = {relevant_combo.rescale}",
                'experiment': 'ATLAS',
                'lumi': 139,
                'com': 13,
                'plot_status': 'Internal',
                'outfile': f"{plot_dir}/MC_v_MC/{relevant_combo.variable}__{relevant_combo.region}_{relevant_combo.rescale}.pdf",
                'main_yrange': None,
                'main_ylog': None,
                'main_ylabel': 'Fraction of Total Events/bin',
                'main_ynorm': True,
                'ratio_ylabel': 'Alt/Ref'
            }

            mcmc_stack = deepcopy(mc_stack)
            mcmc_stack.stack = False
            mcmc_stack.bar_type = 'step'
            mcmc_plot = CoffeaPlot(mcmc_stack, mc_over_mc_ratio, **mcmc_settings)
            mcmc_plot.plot()