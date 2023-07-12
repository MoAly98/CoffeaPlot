
import os, re
from glob import glob
import awkward as ak

LOOK_IN = ['/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16a_nom/',
           '/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16d_nom/',
           '/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16e_nom/',
           '/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3_1/data_nom/'
           ]

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
        for plot in to_plot:
            plot.set_dim(self.dim)

        self.to_plot = to_plot

    def append(self, plot_histo):
        plot_histo.set_dim(self.dim)
        self.to_plot.append(plot_histo)

class Plot(object):
    def __init__(self, name, howto, binning, label, regions=['.*'], idx_by = 'event'):
        self.name = name
        self.howto = howto
        self.binning = binning
        self.label = label
        self.regions = regions
        self.idx = idx_by
        self.dim = None
        assert self.idx in ['event','nonevent']
    def set_dim(self, dim):
        self.dim = dim

class Sample(object):
    def __init__(self, name, regexes, cut_howto, weight_howto, color, label):

        self.name = name

        # Get files for sample
        self.files = self.create_fileset(regexes)
        assert self.files != [], f'NO files found for sample {self.name} with any regexes: {regex}'

        # Set sample cuts
        self.sel = cut_howto

        # Set sample weight
        self.weight = weight_howto

        self.color = color
        self.label = label

    def create_fileset(self, regexes):
        # Collect Regexes
        to_glob = []
        for direc in LOOK_IN:
            to_glob.extend([f'{direc}/{regex}.root' for regex in regexes])

        # Collect files
        globbed   = []
        for wild in to_glob:
            globbed.extend(glob(wild))

        return globbed

class Region(object):
    def __init__(self, name, howto):
        self.name = name
        self.sel = howto

class Rescales(object):
    def __init__(self, name, affected_samples_names, howto):
        self.name   = name
        self.affect = affected_samples_names
        self.method = howto
        assert isinstance(self.method, Functor), "Rescale howto must be a functor"
        assert 'weights' in self.method.args, "A branch called weights must be in data and passed to functor for rescaling"
