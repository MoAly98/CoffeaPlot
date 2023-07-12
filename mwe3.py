from coffea import processor
from coffea.nanoevents import  BaseSchema
import os
os.environ["MALLOC_TRIM_THRESHOLD_"] = "65536"
from glob import glob
from collections import defaultdict


class Functor(object):
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
        assert isinstance(self.args, list)

    def evaluate(self, data):
        data_args = [data[arg] for arg in self.args]
        return self.fn(*data_args)

class Plots(object):
    def __init__(self, dim, tree, to_plot = []):
        if dim != 1 and dim != 2:
            print("ERROR:: Supporting only 1D and 2D plots")
            exit()
        self.dim = dim
        self.tree = tree
        self.to_plot = to_plot

    def append(self, plot_histo):
        plot_histo.set_dim(self.dim)
        self.to_plot.append(plot_histo)

class Plot(object):
    def __init__(self, name, howto, binning):
        self.name = name
        self.howto = howto
        self.binning = binning


class MyProcessor(processor.ProcessorABC):

    def __init__(self, plots = []):
        self.plots =    plots

    def dd(self):
        return defaultdict(dict)

    def process(self, presel_events):

        output_1d = defaultdict(self.dd)
        print(plots_list)
        dataset = presel_events.metadata['dataset']
        print(output_1d)
        print(dataset)

        return {dataset: {'1D': dict(output_1d)}}

    def postprocess(self, accumulator):
        pass


myplot = Plot('new_bdt_tH', Functor(lambda x: x[:,0], ['BDT']), [0, 0.3528, 0.6, 0.78, 1])
plots_list = [ Plots(1, 'nominal_Loose', myplot) ]

if __name__ == '__main__':

    fileset = {'tH': glob('/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16a_nom/346676*.root')}
    executor = processor.FuturesExecutor(workers=1)
    run = processor.Runner(executor=executor, metadata_cache={}, schema=BaseSchema, skipbadfiles=True, maxchunks=1)
    _ = run(fileset, 'nominal_Loose', MyProcessor(plots_list)  )

    print(_)
