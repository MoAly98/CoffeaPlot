# Coffea imports
from coffea import processor
from coffea.nanoevents import  BaseSchema

# IO and Processing imports
import awkward as ak
import uproot
import numpy as np

# Histogramming imports
import hist

# Standard Python imports
import os, re
from pprint import pprint
import cloudpickle as pickle
from copy import deepcopy
from collections import defaultdict

os.environ["MALLOC_TRIM_THRESHOLD_"] = "65536"


from classes import Histogram, Histograms

PROCESS = True

class MyProcessor(processor.ProcessorABC):

    def __init__(self, variables_list, samples_list, regions_list, rescales_list):
        self.variables_list = variables_list
        self.samples_list = samples_list
        self.regions_list = regions_list
        self.rescales_list = rescales_list

    def dd(self):
        return defaultdict(dict)

    def process(self, presel_events):

        accum = Histograms()
        dataset = presel_events.metadata['dataset']

        for a_sample in self.samples_list:
            if dataset != a_sample.name: continue

            sample = a_sample
            break

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

                if all(re.match(region_to_use, region_to_plot.name) is None for region_to_use in regions_to_use): continue

                filt_reg = filt_sample[region_to_plot.sel.evaluate(filt_sample)]


                # ================ Empty histogram for this region for this sample ===========
                if ak.num(filt_reg['weights'], axis=0) == 0:
                    return accum

                # =============== Non empty histogram for this region for this sample ==========
                if variable.dim == 1:

                    for rescaling in self.rescales_list:

                        h = hist.Hist.new.Var(binning, name = name, label=label, flow=True).Weight()

                        if re.match(rescaling.affect, sample.name) is not None:
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
                        if sample.type != 'DATA':
                            tot_histo_obj = Histogram(name, deepcopy(h), 'total', region_to_plot.name , rescaling.name)
                        else:
                            tot_histo_obj = Histogram(name, 0, 'total', region_to_plot.name , rescaling.name)
                        accum[samp_histo_obj] = samp_histo_obj
                        accum[tot_histo_obj] = tot_histo_obj

                else:
                    # TODO:: 2D
                    pass

        return accum

    def postprocess(self, accumulator):
        pass

if __name__ == '__main__':

    fileset = {}
    for sample in samples_list:
        fileset[sample.name] = sample.files

    tree_to_plot_list = {plots_list.tree: [] for plots_list in plots_to_make}
    for plots_list in plots_to_make:
        tree_to_plot_list[plots_list.tree].extend(plots_list)

    executor = processor.FuturesExecutor(workers=8)

    for tree, plots_list in tree_to_plot_list.items():
        dump_to = f"outputs/data-test5/"
        os.makedirs(dump_to, exist_ok=True)
        if PROCESS:
            run = processor.Runner(executor=executor, metadata_cache={}, schema=BaseSchema, skipbadfiles=True)
            coffea_out = run(fileset, tree, MyProcessor(plots_list, samples_list, regions_list, rescales_list))

            coffea_out = dict(coffea_out.to_plot)

            with open(f"{dump_to}/data___{tree}.pkl", "wb") as f:
                pickle.dump(dict(coffea_out), f)
        else:
            with open(f"{dump_to}/data___{tree}.pkl", "rb") as f:
                coffea_out = pickle.load(f)

        # ====== Loop over 1D plots ====== #
        pprint(coffea_out)