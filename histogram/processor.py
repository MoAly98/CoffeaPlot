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
from containers.variables import Eff

class CoffeaPlotProcessor(processor.ProcessorABC):

    def __init__(self, CoffeaPlotSettings):
        self.variables_list = CoffeaPlotSettings.variables_list
        self.samples_list   = CoffeaPlotSettings.samples_list
        self.regions_list   = CoffeaPlotSettings.regions_list
        self.rescales_list  = CoffeaPlotSettings.rescales_list
        self.pie_sumsample  = CoffeaPlotSettings.piechart_plot_settings.sumsample
        self.pie_samples    = CoffeaPlotSettings.piechart_plot_settings.samples

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

                # For efficiency-type variables, we compute 2 histograms,
                # one for the numerator and one for the denominator
                if isinstance(variable, Eff):
                    # Numerator and denominator are differentiated by selections
                    eff_mask_functor = variable.numsel if ':Num' in name else variable.denomsel

                for region_to_plot in self.regions_list:

                    if all(re.match(region_to_use, region_to_plot.name) is None for region_to_use in regions_to_use): continue

                    filt_reg = filt_sample[region_to_plot.sel.evaluate(filt_sample)]

                    # Get the bool mask for the efficiency variable component
                    if isinstance(variable, Eff):
                        eff_mask = eff_mask_functor.evaluate(filt_reg)

                    # ================ Empty histogram for this region for this sample ===========
                    if ak.num(filt_reg['weights'], axis=0) == 0:
                        continue

                    # =============== Non empty histogram for this region for this sample ==========
                    if variable.dim == 1:

                        for rescaling in self.rescales_list:

                            h = hist.Hist.new.Var(binning, name = name, label=label, flow=True).Weight()

                            if any(re.match(affected_sample, sample.name) is not None for affected_sample in rescaling.affects):
                                rescaled_weights = rescaling.method.evaluate(filt_reg)
                            else:
                                rescaled_weights = filt_reg['weights']

                            if idxing == 'nonevent':
                                # Compute variable of interest
                                var = histo_compute.evaluate(filt_reg)
                                # Expect all args going into the histogram variable have same shape, make weights have same shape
                                w, _ = ak.broadcast_arrays(rescaled_weights[:, np.newaxis], filt_reg[histo_compute.args[0]])
                                # TODO:: Make this more general than just flattening operations
                                w = ak.flatten(w)

                                if isinstance(variable, Eff):
                                    var = var[eff_mask]
                                    w   = w[eff_mask]

                            else:
                                var = histo_compute.evaluate(filt_reg)
                                w = rescaled_weights
                                if isinstance(variable, Eff):
                                    var = var[eff_mask]
                                    w   = w[eff_mask]

                            # Fill the histogram
                            h.fill(var, weight = w)

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

        for a_sample in self.samples_list:

            if isinstance(a_sample, SuperSample):   samples = a_sample.subsamples
            else:   samples = [a_sample]

            sample_names = [sample.name for sample in samples]+['total']
            for region_to_plot in self.regions_list:
                for rescaling in self.rescales_list:
                    for sample in sample_names:
                        done_vars = []



                        for variable in self.variables_list:

                            if self.pie_samples is not None and sample.name in self.pie_samples:
                                sumsample_histogram  = accumulator[(variable.name, self.pie_sample, region_to_plot.name , rescaling.name)]
                                pie_sample_histogram = accumulator[(variable.name, sample, region_to_plot.name , rescaling.name)]

                                fraction = pie_sample_histogram.values().sum()/sumsample_histogram.values().sum()

                                err1 = pie_sample_histogram.variances().sum()/pie_sample_histogram.values().sum()**2
                                err2 = sumsample_histogram.variances().sum()/sumsample_histogram.values().sum()**2
                                err = fraction*np.sqrt(err1 + err2)

                                hcat = hist.Hist.new.StrCat([pie_sample_histogram.sample], name="c", label=pie_sample_histogram.label).Weight()
                                hcat.fill([pie_sample_histogram.sample], weight=fraction)
                                hcat.variances()[0] = err

                                cat_histo = Histogram(variable.name+":pie", hcat, sample.name, region.name , rescale.name)
                                accumulator[cat_histo] = cat_histo

                            if isinstance(variable, Eff):
                                variable_name = variable.name.replace(':Num', '').replace(':Denom', '')
                                if variable_name in done_vars: continue

                                numerator   = accumulator[(variable_name+":Num", sample, region_to_plot.name , rescaling.name)]
                                denominator = accumulator[(variable_name+":Denom", sample, region_to_plot.name , rescaling.name)]

                                eff  = np.divide(numerator.values(), denominator.values(), out=np.zeros_like(numerator.values()), where=denominator.values()!=0)

                                err1 = (1. - 2. * eff) * numerator.variances()
                                err2 = (eff**2) * np.divide(denominator.variances(), denominator.values()**2, out=np.zeros_like(denominator.values()), where=denominator.values()!=0)
                                err3 = np.divide(1, denominator.values()**2, out=np.zeros_like(denominator.values()), where=denominator.values()!=0)
                                errsq  = abs((err1+err2)*err3)

                                binning = numerator.h.axes[0].edges
                                hnew = hist.Hist.new.Variable(binning, name=variable.name, label=variable.label).Weight()
                                hnew[...] = np.stack([eff, errsq], axis=-1)

                                eff_histo = Histogram(variable_name, hnew, sample, region_to_plot.name , rescaling.name)
                                accumulator[eff_histo] = eff_histo

                                done_vars.append(variable_name)
        return accumulator
