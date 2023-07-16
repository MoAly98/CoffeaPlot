
import os, re
from glob import glob
import awkward as ak
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
    def __init__(self, name, stype, regexes, cut_howto, weight_howto, color, label, category = None):

        # Sample name
        self.name = name

        # Sample type
        assert stype.upper() in ['BKG','SIG','DATA'], "ERROR:: Sample type must be BKG, SIG, or DATA (case in-sensitive)"

        self.type = stype.upper()

        # Sample category
        self.category = category

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

    def __init__(self, name, histo, sample, region, rescale, label = None):

        self.name   = name
        self.h = histo
        self.sample = sample
        self.region = region
        self.rescale = rescale
        self.label = label

        self.stylish_sample = None
        self.stylish_region = None
        self.stylish_rescale = None

    def set_label(self, label):
        self.label = label

    def set_stylish_sample(self, sample):
        self.stylish_sample = sample

    def set_stylish_region(self, region):
        self.stylish_region = region

    def set_stylish_rescale(self, rescale):
        self.stylish_rescale = rescale

    def variances(self):
        return self.h.variances()

    def values(self):
        return self.h.values()

    def __eq__(self, other):
        return (self.name == other.name) and (self.sample == other.sample) and (self.region == other.region) and (self.rescale == other.rescale)

    def cross_sample_add(self, other):
        print(self.region, other.region)
        print(self.name, other.name)
        print(self.rescale, other.rescale)
        if self.region == other.region and self.name == other.name and self.rescale == other.rescale:

            self.h += other.h
        return self

    def __add__(self, other):
        if self.name == other.name:
            self.h += other.h
        return self


    def __radd__(self, other):
        '''
        Required for use of sum() function. This
        will add histogramsa cross sample borders
        to be used in plotting.
        '''
        if other == 0:
            return Histogram(self.name, self.h.copy(), 'TempSample', self.region, self.rescale)
        else:
            return self.__add__(other)

    def __repr__(self):
        return f'{self.name}__{self.sample}__{self.region}__{self.rescale}'

    def __str__(self):
            return f'Hist: {self.name}, Sample: {self.sample}, Region: {self.region}, Rescale: {self.rescale}'

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

        if isinstance(histo, Histogram):
            key = (histo.name, histo.sample, histo.region, histo.rescale)
        else:
            key = histo
        self.to_plot[key] = h

#TODO:: Systematics?