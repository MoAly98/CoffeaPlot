
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

# TODO:: Specify type of sample
# TODO:: Class for Stack and Stackatino (Stack element)
# TODO:: Specify Normalised Signal
# TODO:: Specify fraction of plot used by ratio plot
# TODO:: Specify ratio plot limits
# TODO:: Specify figure size
# TODO:: Specify ylabel
# TODO:: Specify legend location
# TODO:: Sample categories
# TODO:: Nominal rescale should be added in __init__ using regex for affected samples and processor should use regex match

log = logger()
# Stuff user should give me?
dump_to = f"outputs/"

BLIND_ON = ['tH','tWH']
log.info(f"Blinding using {BLIND_ON}")
DATA_NAME = 'Data'
log.info(f"Assuming data sample is called {DATA_NAME}")

# Stuff i do not need from user
data_dir = f"{dump_to}/data/"
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
        os.makedirs(f"{plot_dir}/DataMC/{tree}/",       exist_ok=True)
        os.makedirs(f"{plot_dir}/Normalised/{tree}/",   exist_ok=True)


        # ====== Loop over 1D plots ====== #

        stacks = []
        data_stacks = []
        datamc_ratios = []
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
                for rescale in rescales_list:
                    log.info(f"Setting up rescale {rescale.name}")

                    # ============== Create 1x Stack per region, rescaling, variable ============== #
                    stack        = Stack(bar_type = 'stepfilled', error_type = 'stat')
                    data_stack   = Stack(bar_type = 'point', error_type = 'stat')
                    datamc_ratio = RatioPlot(bar_type = 'step', error_type = 'stat')
                    signif_ratio = RatioPlot(bar_type = 'stepfilled', error_type = 'stat')

                    # ============== Group together samples in different ways ============== #
                    category_to_samples = defaultdict(list)

                    backgrounds = []
                    signals = []
                    region_targets = []
                    data = None

                    for sample in samples_list:
                        # ============== Group samples from same category ============== #
                        if sample.category is not None:
                            category_to_samples[sample.category].append(sample)
                        else:
                            category_to_samples[sample.name].append(sample)

                        # ============== Group samples by type ============== #
                        if any(re.match(region_target_name, sample.name) for region_target_name in region_targets_names):
                            log.info(f"Adding sample {sample.name} to region {region.name} targets")
                            region_targets.append(sample)

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
                        log.error("No data sample found")

                    # ============== Total Histo ============== #
                    total_histogram =  histograms[(variable.name, 'total', region.name, rescale.name)]

                    # ============== Backgrounds Histo ============== #
                    backgrounds_histograms = [histograms[(variable.name, background.name, region.name, rescale.name)] for background in backgrounds]
                    tot_backgrounds_histogram = sum(backgrounds_histograms)

                    # ============== Signal Histo ============== #
                    signals_histograms = [histograms[(variable.name, signal.name, region.name, rescale.name)] for signal in signals]
                    tot_signals_histogram = sum(signals_histograms)

                    # ============== Data Histo ============== #
                    data_histogram  =  histograms[(variable.name, data.name,  region.name, rescale.name)]

                    # ============== Data Stack ============== #
                    data_stackicino = Stackatino([data_histogram], label = data.name, color = 'black')
                    data_stack.append(data_stackicino)

                    # ============== Set up a DataMC ratio plot ============== #
                    datamc_ratioitem = RatioItem(data_histogram, total_histogram, label = None, ylabel = 'Data/MC', marker = 'o', color = 'black')
                    datamc_ratio.append(datamc_ratioitem)

                    # TODO:: somehow allow user to ask for more data/mc style plots (e.g. MC subtraction, one specific MC, .. )

                    # ============== Set up significance ratio plots ============== #
                    for target in region_targets:
                        target_histogram = histograms[(variable.name, target.name, region.name, rescale.name)]
                        signif_ratioitem = RatioItem(target_histogram, tot_backgrounds_histogram, ylabel = rf'{target.name}/$\sqrt(B)$', color = target.color, alpha = 0.8)
                        signif_ratio.append(signif_ratioitem)

                    # ============== Blinding ============== #
                    stack.blinder = Blinder(tot_signals_histogram, tot_backgrounds_histogram, threshold = 0.00333)
                    # ============== Make a Stackatino for each category ============== #
                    for category, samples in category_to_samples.items():
                        log.info(f"Setting up category {category}")
                        stackatinos = Stackatino(label = category)
                        for sample in samples:
                            histogram = histograms[(variable.name, sample.name, region.name, rescale.name)]
                            stackatinos.append(histogram)

                        stack.append(stackatinos)

                    # ============== Append each Stack to corresponding list of Stacks ============== #
                    stacks.append(stack)
                    data_stacks.append(data_stack)
                    datamc_ratios.append(datamc_ratio)
                    signif_ratios.append(signif_ratio)

        # ====== How many plots to make? ====== #
        num_plots = len(stacks) # x2 for DataMC and Significance

        # ======= Now we make 2 StackPlots per region, rescaling, variable ======= #
        # One for DataMC, one for Significance

        # ====== Loop over stacks ========= #
        for plot_idx in range(num_plots):
            pass












        # histos_1d  = coffea_out['1D']
        # for region_name, hnames_to_histos in histos_1d.items():
        #     region = plot_regions.get_region(region_name)
        #     if region is None: print("ERROR:: Region not found", region_name); exit(1)
        #     region_targets = region.targets
        #     if region_targets == []: region_targets = BLIND_ON
        #     num_significance_panels = len(region_targets) + 1 # Main plot + 1 per target


        #     for hname, rescalings_to_histos in hnames_to_histos.items():
        #         for plots_list in plots_to_make:
        #             if plots_list.tree != tree: continue
        #             if plots_list.dim != 1:     continue
        #             xlabel = plots_list.get_plot(hname).label


        #         for rescale_name, samples_to_histos in rescalings_to_histos.items():
        #             rescale = plot_rescales.get_rescale(rescale_name)
        #             if rescale is None: print("ERROR:: Rescale not found", rescale_name); exit(1)

        #             # ====== Update samples for all histograms to use lateset colors and labels ====== #
        #             for sample_name, histo in samples_to_histos.items():
        #                 if sample_name == 'total': continue
        #                 sample = plot_samples.get_sample(sample_name)
        #                 if sample is None : print("ERROR:: Sample not found", sample_name); exit(1)

        #                 histo.sample = sample

        #             signal_for_blinding       = sum(samples_to_histos[blinding_signal].h for blinding_signal in BLIND_ON)
        #             backgrounds_for_blinding  = sum([histo.h for sample, histo in samples_to_histos.items() if sample not in BLIND_ON and sample != DATA_NAME and sample != 'total'])
        #             blind_bool                = get_blinding(signal_for_blinding, backgrounds_for_blinding)

        #             # ====== Make stacked histogram with significance per bin in secondary panels ====== #

        #             signif_fig, signif_main_ax, signif_axs = create_fig_with_n_panels(1, num_significance_panels)

        #             data_h = samples_to_histos[DATA_NAME]

        #             to_stack = []
        #             for sample_name, histo in samples_to_histos.items():
        #                 histo.set_label(xlabel)
        #                 if sample_name == DATA_NAME: continue
        #                 if sample_name == 'total': continue
        #                 to_stack.append(histo)

        #             plot_stack(to_stack, data_h, signif_main_ax, blind_bool, title = f'Region = {region.name} and Rescaling = {rescale.name}')

        #             for i, target in enumerate(region_targets):
        #                 is_last_target = (i == len(signif_axs) - 1)
        #                 target_histo = samples_to_histos[target]

        #                 non_target_histo  = sum([histo.h for sample, histo in samples_to_histos.items() if sample != target and sample != DATA_NAME])

        #                 # We compute signficance per bin and plot it
        #                 signif, signif_err = get_signif_per_bin(target_histo.h, non_target_histo)
        #                 plot_signif_per_bin(target_histo, signif, signif_err, signif_axs[i], is_last_target)

        #             signif_fig.savefig(f"{plot_dir}/Significance/{tree}/{region.name}_{hname}_{rescale_name}.pdf", bbox_inches="tight")

        #             plt.clf()
        #             plt.close('all')

        #             # ====== Make stacked histogram with data/mc ratio per bin in secondary panels ====== #
        #             datamc_fig, datamc_main_ax, datamc_ax  = create_fig_with_n_panels(1, 2, h_ratio=[1,0.2])

                    # for sample_name, dim_to_histos in samples_to_histos.items():
                    #     histos_1d = dim_to_histos['1D']

                    #     sample = plot_samples.get_sample(sample_name)
                    #     if sample_name == 'total':
                    #         sample = Sample('tot', None, None, None, 'black', 'Total MC')


