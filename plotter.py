
from classes import *
from  samples import *
from regions import *
from rescalings import *
from variables import *
from utils import *
from plot_utils import *

import os
import pickle
import numpy as np

# Stuff user should give me?
dump_to = f"outputs/"
BLIND_ON = 'tH'
DATA_NAME = 'Data'


# Stuff i do not need from user
data_dir = f"{dump_to}/data/"
plot_dir = f"{dump_to}/plots/"

plot_rescales.append(Rescale('ProtNominal', [''], Functor(lambda w: w, ['weights'])))

for (root, _, files) in os.walk(f'{data_dir}', topdown=True):
    for file in files:
        if not file.endswith('.pkl') or "___" not in file:   continue

        tree = file.split('___')[1].split('.')[0]


        with open(f"{data_dir}/{file}", "rb") as f:
            coffea_out = pickle.load(f)

        # ====== Create directories ====== #
        os.makedirs(f"{plot_dir}/Tables/{tree}/",       exist_ok=True)
        os.makedirs(f"{plot_dir}/Significance/{tree}/", exist_ok=True)
        os.makedirs(f"{plot_dir}/Separation/{tree}/",   exist_ok=True)
        os.makedirs(f"{plot_dir}/DataMC/{tree}/",       exist_ok=True)
        os.makedirs(f"{plot_dir}/Normalised/{tree}/",   exist_ok=True)


        # ====== Loop over 1D plots ====== #

        histos_1d  = coffea_out['1D']
        for region_name, hnames_to_histos in histos_1d.items():
            region = plot_regions.get_region(region_name)
            if region is None: print("ERROR:: Region not found", region_name); exit(1)
            region_targets = region.target
            num_significance_panels = len(region_targets) + 1 # Main plot + 1 per target


            for hname, rescalings_to_histos in hnames_to_histos.items():
                for plots_list in plots_to_make:
                    if plots_list.tree != tree: continue
                    if plots_list.dim != 1:     continue
                    xlabel = plots_list.get_plot(hname)


                for rescale_name, samples_to_histos in rescalings_to_histos.items():
                    rescale = plot_rescales.get_rescale(rescale_name)
                    if rescale is None: print("ERROR:: Rescale not found", rescale_name); exit(1)

                    signal_for_blinding       = samples_to_histos[BLIND_ON].h
                    backgrounds_for_blinding  = sum([histo.h for sample, histo in samples_to_histos.items() if sample != BLIND_ON])
                    blind_bool                = get_blinding(signal_for_blinding, backgrounds_for_blinding)

                    # ====== Make stacked histogram with significance per bin in secondary panels ====== #

                    signif_fig, signif_main_ax, signif_axs = create_fig_with_n_panels(1, num_significance_panels)



                    data_h = samples_to_histos[DATA_NAME]

                    to_stack = []
                    for sample_name, histo in samples_to_histos.items():
                        histo.set_label(xlabel)
                        if sample_name == DATA_NAME: continue
                        if sample_name == 'total': continue
                        to_stack.append(histo)

                    plot_stack(to_stack, data_h, signif_main_ax, blind_bool, title = f'Region = {region.name} and Rescaling = {rescale.name}')


                    signif_fig.savefig(f"{plot_dir}/Significance/{tree}/{region}_{histoname}.pdf")


                    # ====== Make stacked histogram with data/mc ratio per bin in secondary panels ====== #
                    datamc_fig, datamc_main_ax, datamc_ax  = create_fig_with_n_panels(1, 2, h_ratio=[1,0.2])

                    # for sample_name, dim_to_histos in samples_to_histos.items():
                    #     histos_1d = dim_to_histos['1D']

                    #     sample = plot_samples.get_sample(sample_name)
                    #     if sample_name == 'total':
                    #         sample = Sample('tot', None, None, None, 'black', 'Total MC')





                    print("Hi")



