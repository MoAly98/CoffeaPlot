import awkward as ak
from coffea import processor
import coffea
from coffea.nanoevents import  BaseSchema
import hist
from collections import defaultdict
import uproot
import numpy as np
import pandas as pd
#import seaborn as sns
import os
from pprint import pprint
import cloudpickle as pickle
os.environ["MALLOC_TRIM_THRESHOLD_"] = "65536"


from classes import *
from  samples import *
from regions import *
from rescalings import *
from variables import *
from utils import *

PROCESS = True
DATA_NAME = 'Data'

# TODO:: Histograms class to support accumlation -- storage option

class MyProcessor(processor.ProcessorABC):

    def __init__(self, variables_list, samples_list, regions_list, rescales_list):
        self.variables_list = variables_list
        self.samples_list = samples_list
        self.regions_list = regions_list
        self.rescales_list = rescales_list


    def dd(self):
        return defaultdict(dict)


    def process(self, presel_events):

        #output_1d =  defaultdict(self.dd)
        accum = Histograms()
        output_2d = defaultdict(self.dd)
        dataset = presel_events.metadata['dataset']

        for a_sample in self.samples_list:
            if dataset != a_sample.name: continue

            sample = a_sample
            break

        self.rescales_list.append(Rescale('ProtNominal', [sample.name], Functor(lambda w: w, ['weights']) ) )
        sample_weights = sample.weight.evaluate(presel_events) if sample.weight is not None else 1.0

        presel_events['weights'] = sample_weights
        filt_sample = presel_events[sample.sel.evaluate(presel_events)] if sample.sel is not None else presel_events

        # ====== Loop over 1D plots ====== #

        for variable in self.variables_list:
            name           = variable.name
            regions_to_use = variable.regions
            idxing         = variable.idx
            binning        = variable.binning
            label          = variable.label
            histo_compute  = variable.howto

            for region_to_plot in self.regions_list:

                if all(re.match(region_to_use, region_to_plot.name) is None and region_to_use != 'all' for region_to_use in regions_to_use): continue

                filt_reg = filt_sample[region_to_plot.sel.evaluate(filt_sample)]


                # ================ Empty histogram for this region for this sample ===========
                if ak.num(filt_reg['weights'], axis=0) == 0:
                    for rescaling in self.rescales_list:
                        accum[Histogram(name, h, 'total', region_to_plot.name , rescaling.name)] =  hist.Hist.new.Var(binning, name = name, label=label, flow=True).Weight()
                        accum[Histogram(name, h, 'total', region_to_plot.name , rescaling.name)] =  hist.Hist.new.Var(binning, name = name, label=label, flow=True).Weight()

                        # TODO:: Need to add 2D histo here
                        # output_1d[region_to_plot.name][rescaling.name][name] = hist.Hist.new.Var(binning, name = name, label=label, flow=True).Weight()
                        # output_2d[region_to_plot.name][rescaling.name][name] = None # Need empty 2D histo here
                    return accum

                # =============== Non empty histogram for this region for this sample ==========
                if variable.dim == 1:

                    for rescaling in self.rescales_list:

                        h = hist.Hist.new.Var(binning, name = name, label=label, flow=True).Weight()

                        if sample.name in rescaling.affect:
                            rescaled_weights = rescaling.method.evaluate(filt_reg)
                        else:
                            rescaled_weights = filt_reg['weights']

                        if idxing == 'nonevent':
                            assert len(histo_compute.args) == 1, "Composite variables are not supported when indexing by nonevent"

                            w, arg = ak.broadcast_arrays(rescaled_weights[:, np.newaxis], filt_reg[histo_compute.args[0]])
                            data = histo_compute.fn(arg)
                            w = ak.flatten(w)
                        else:
                            data = histo_compute.evaluate(filt_reg)
                            w = rescaled_weights

                        # Fill the histogram
                        h.fill(data, weight = w)
                        # Save the histogram
                        samp_histo_obj = Histogram(name, h, dataset, region_to_plot.name , rescaling.name)
                        tot_histo_obj = Histogram(name, h.copy(), 'total', region_to_plot.name , rescaling.name)
                        #output_1d[region_to_plot.name][rescaling.name][name] = h
                        accum[samp_histo_obj] = samp_histo_obj.h
                        accum[tot_histo_obj] = tot_histo_obj.h

                else:
                    # TODO:: 2D
                    pass

        return accum

    def postprocess(self, accumulator):


        # # ====== Loop over 1D plots ====== #
        # total_hists = dd()

        # for dataset, dim_to_histos in accumulator.items():
        #     if dataset == DATA_NAME: continue

        #     regions_to_histos = dim_to_histos['1D']

        #     for region, scaling_to_histos in regions_to_histos.items():
        #         for scale, hnames_to_histos in scaling_to_histos.items():
        #             for hname, histo in hnames_to_histos.items():

        #                 total_hists['total']['1D'][region][scale][hname] += histo
        #                 accumulator[dataset]['1D'][region][scale][hname] = Histogram(hname, histo, self.samples_list.get_sample(dataset), self.regions_list.get_region(region), self.rescales_list.get_rescale(scale))

        # accumulator['total'] = dict(total_hists['total'])

        # sample_tot = Sample('tot', None, None, None, 'black', 'Total MC')
        # regions_to_histos = accumulator['total']['1D']
        # for region, scaling_to_histos in regions_to_histos.items():
        #     for scale, hnames_to_histos in scaling_to_histos.items():
        #         for hname, histo in hnames_to_histos.items():
        #             accumulator['total']['1D'][region][scale][hname] = Histogram(hname, histo, sample_tot, region, self.rescales_list.get_rescale(scale))

        # return accumulator
        pass

if __name__ == '__main__':

    fileset = {}
    for sample in samples_list:
        fileset[sample.name] = sample.files

    tree_to_plot_list = {plots_list.tree: [] for plots_list in plots_to_make}
    for plots_list in plots_to_make:
        tree_to_plot_list[plots_list.tree].extend(plots_list)

    executor = processor.FuturesExecutor(workers=8)
    #executor = processor.IterativeExecutor()
    for tree, plots_list in tree_to_plot_list.items():
        dump_to = f"outputs/"
        os.makedirs(dump_to, exist_ok=True)
        if PROCESS:
            run = processor.Runner(executor=executor, metadata_cache={}, schema=BaseSchema, skipbadfiles=True)
            coffea_out = run(fileset, tree, MyProcessor(plots_list, samples_list, regions_list, rescales_list))

            # reordered_map = defaultdict(deep_map)
            # for dataset, dim_to_histos in coffea_out.items():
            #     for dim, regions_to_histos in dim_to_histos.items():
            #         for region, scalings_to_histos in regions_to_histos.items():
            #             for scaling, hnames_to_histos in scalings_to_histos.items():
            #                 for hname, histo in hnames_to_histos.items():
            #                     reordered_map[dim][region][hname][scaling][dataset] = histo

            coffea_out = dict(coffea_out.to_plot)


            with open(f"{dump_to}/data/data___{tree}.pkl", "wb") as f:
                pickle.dump(dict(coffea_out), f)
        else:
            with open(f"{dump_to}/data/data___{tree}.pkl", "rb") as f:
                coffea_out = pickle.load(f)

        # ====== Loop over 1D plots ====== #
        pprint(coffea_out)
        print(coffea_out[('new_bdt_tH', 'total', 'SR' , 'ProtNominal')].values())
        print(coffea_out[('new_bdt_tH', 'tH',    'SR' , 'ProtNominal')].values())
        print(coffea_out[('new_bdt_tH', 'tWH',   'SR' , 'ProtNominal')].values())
