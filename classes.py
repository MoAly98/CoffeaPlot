
import os, re
from glob import glob
import awkward as ak
from collections import MutableMapping
from coffea.processor import AccumulatorABC


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

class Variable(object):
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

    def __eq__(self, other):
        return self.name == other.name

class Variables(object):
    def __init__(self, dim, tree, to_plot = []):
        if dim != 1 and dim != 2:
            print("ERROR:: Supporting only 1D and 2D variables")
            exit()
        self.dim = dim
        self.tree = tree
        for variable in to_plot:
            variable.set_dim(self.dim)

        self.to_plot = to_plot

    def append(self, variable):
        variable.set_dim(self.dim)
        self.to_plot.append(variable)

    def get_variable(self, name):
        for variable in self.to_plot:
            if variable.name == name:
                return variable
        return None

    def __iter__(self):
        for variable in self.to_plot:
            yield variable

class Sample(object):
    def __init__(self, name, regexes, cut_howto, weight_howto, color, label):

        self.name = name

        # Get files for sample
        if regexes is not None:
            self.files = self.create_fileset(regexes)
            assert self.files != [], f'NO files found for sample {self.name} with any regexes: {regex}'
        else:
            self.files = None
        # Set sample cuts
        self.sel = cut_howto

        # Set sample weight
        self.weight = weight_howto

        self.color = color
        self.label = label

    def __eq__(self, other):
        return self.name == other.name

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

class Samples(object):
    def __init__(self, to_plot = []):
        self.to_plot   = to_plot

    def append(self, sample):
        self.to_plot.append(sample)

    def get_sample(self, name):
        for sample in self.to_plot:
            if sample.name == name:
                return sample
        return None

    def __iter__(self):
        for sample in self.to_plot:
            yield sample

class Region(object):
    def __init__(self, name, howto, target_sample = []):
        self.name = name
        self.sel = howto
        self.targets = target_sample

    def __eq__(self, other):
        return self.name == other.name


class Regions(object):
    def __init__(self, to_plot = []):
        self.to_plot   = to_plot

    def append(self, region):
        self.to_plot.append(region)

    def get_region(self, name):
        for region in self.to_plot:
            if region.name == name:
                return region
        return None

    def __iter__(self):
        for region in self.to_plot:
            yield region

class Rescale(object):
    def __init__(self, name, affected_samples_names, howto):
        self.name   = name
        self.affect = affected_samples_names
        self.method = howto
        assert isinstance(self.method, Functor), "Rescale howto must be a functor"
        assert 'weights' in self.method.args, "A branch called weights must be in data and passed to functor for rescaling"

    def __eq__(self, other):
        return self.name == other.name


class Rescales(object):
    def __init__(self, to_plot = []):
        self.to_plot   = to_plot

    def append(self, rescale):
        self.to_plot.append(rescale)

    def get_rescale(self, name):
        for rescale in self.to_plot:
            if rescale.name == name:
                return rescale
        return None

    def __iter__(self):
        for rescale in self.to_plot:
            yield rescale

class Histogram(object):

    def __init__(self, name, histo, sample, region, rescale):

        self.name   = name
        self.h = histo
        self.sample = sample
        self.region = region
        self.rescale = rescale
        self.label = None


    def set_label(self, label):
        self.label = label

    def __eq__(self, other):
        return (self.name == other.name) and (self.sample == other.sample) and (self.region == other.region) and (self.rescale == other.rescale)

    def __add__(self, other):

        if self == other:
            self.h + other.h

        return self

class Histograms(AccumulatorABC):
    def __init__(self):
        # Initialize any necessary data structures or variables for your accumulator
        self.to_plot = {}

    def add(self, other):
        # Implement the addition logic to combine histograms
        for key, value in other.to_plot.items():
            if key in self.to_plot:
                # Add the histograms together or define your own custom logic
                self.to_plot[key] += value
            else:
                # Initialize the histogram in the accumulator if it doesn't exist
                self.to_plot[key] = value

    def identity(self):
        # Create and return a new instance of the accumulator
        return Histograms()

    def clone(self):
        # Create a copy of the accumulator
        acc = MyAccumulator()
        acc.histograms = self.to_plot.copy()
        return acc

    def __setitem__(self, histo, h ):
        key = (histo.name, histo.sample, histo.region, histo.rescale)
        self.to_plot[key] = h


# class Histograms(dict):
#     def __init__(self, to_plot = {}):
#         self.to_plot = to_plot

#     def identity(self):
#         ret = Histograms()
#         for key, value in self.to_plot.items():
#             ret.to_plot[key] = value.identity()
#         return ret

#     def add(self, other):
#         if isinstance(other, MutableMapping):
#             for key, value in other.to_plot.items():
#                 if key not in self.to_plot:
#                     self.to_plot[key] = value
#                 else:
#                     self.to_plot[key] += value
#         else:
#             raise ValueError

#     def append(self, histo):
#         key = (histo.name, histo.sample, histo.region, histo.rescale)
#         self.to_plot[key] = histo



    # def get_histogram(self, name, sample_name, region_name, rescale_name):
    #     return self.to_plot.get((name, sample_name, region_name, rescale_name), None)

    # def __getitem__(self, key):
    #     return self.to_plot[key]
    # def __setitem__(self, key, value):
    #     self.to_plot[key] = value
    # def __delitem__(self, key):
    #     del self.to_plot[key]
    # def __len__(self):
    #     return len(self.to_plot)
    # def __iter__(self):
    #     return iter(self.to_plot)
    # def __repr__(self):
    #     return repr(self.to_plot)

    # def items(self):
    #     return self.to_plot.items()

    # # def __add__(self, other):
    # #     return self.to_plot + other.to_plot