# Coffea imports
from coffea import processor

# IO and Processing imports
import awkward as ak
import uproot
import numpy as np

# Histogramming imports
import hist

# Standard Python imports
import os, re
from copy import deepcopy
from collections import defaultdict

os.environ["MALLOC_TRIM_THRESHOLD_"] = "65536"

# CoffeaPlot imports
from containers.histograms import Histogram, Histograms
from containers.samples import SuperSample

class CoffeaPlotProcessor(processor.ProcessorABC):

    def __init__(self, CoffeaPlotSettings):
        self.variables_list = CoffeaPlotSettings.variables_list
        self.samples_list = CoffeaPlotSettings.samples_list
        self.regions_list = CoffeaPlotSettings.regions_list
        self.rescales_list = CoffeaPlotSettings.rescales_list

    def dd(self):
        return defaultdict(dict)

    def process(self, presel_events):

        accum = Histograms()
        dataset = presel_events.metadata['dataset']

        for a_sample in self.samples_list:

            if dataset != a_sample.name: continue
            the_sample = a_sample
            break

        if isinstance(the_sample, SuperSample):
            samples = the_sample.subsamples
        else:
            samples = [the_sample]

        for sample in samples:

            presel_events['weights'] = 1.0
            mc_weight = sample.mc_weight.evaluate(presel_events)
            sample_weights = sample.weight.evaluate(presel_events)
            presel_events['weights'] = sample_weights*mc_weight

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

                            if any(re.match(affected_sample, sample.name) is not None for affected_sample in rescaling.affects):
                                rescaled_weights = rescaling.method.evaluate(filt_reg)
                            else:
                                rescaled_weights = filt_reg['weights']

                            if idxing == 'nonevent':
                                if len(histo_compute.args) != 1:
                                    raise NotImplementedError("Composite variables are not supported when indexing by nonevent")
                                w, arg = ak.broadcast_arrays(rescaled_weights[:, np.newaxis], filt_reg[histo_compute.args[0]])
                                data = histo_compute.fn(arg)
                                w = ak.flatten(w)
                            else:
                                data = histo_compute.evaluate(filt_reg)
                                w = rescaled_weights

                            # Fill the histogram
                            h.fill(data, weight = w)

                            # Save the histogram
                            samp_histo_obj = Histogram(name, h, sample.name, region_to_plot.name , rescaling.name)
                            if sample.type != 'DATA':
                                tot_histo_obj = Histogram(name, deepcopy(h), 'total', region_to_plot.name , rescaling.name)
                            else:
                                tot_histo_obj = Histogram(name, 0, 'total', region_to_plot.name , rescaling.name)

                            accum[samp_histo_obj] = samp_histo_obj

                            if sample == samples[0]:
                                accum[tot_histo_obj] = tot_histo_obj
                            else:
                                accum[tot_histo_obj] += tot_histo_obj

                    else:
                        # TODO:: 2D
                        pass

        return accum

    def postprocess(self, accumulator):
        pass