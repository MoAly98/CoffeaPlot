
# Histogramming imports
import hist
import numpy as np
import math
from coffea.processor import AccumulatorABC

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

        self.color = None

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

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            self.h *= other
        elif isinstance(other, Histogram):
            if self.name == other.name:
                self.h *= other.h
        return self

    def __rmul__(self, other):
        return self.__mul__(other)

    def __add__(self, other):
        if isinstance(other, Histogram):
            if self.name == other.name:
                if (self.sample != other.sample and (self.sample != '___DUMMY___' and other.sample != '___DUMMY___')) or self.region != other.region or self.rescale != other.rescale:
                    print("BAD!! Adding histograms", self.sample, other.sample, self.region, other.region, self.rescale, other.rescale)
                self.h += other.h

        elif isinstance(other, (int, float)):
            self.h += other

        return self


    def __radd__(self, other):
        '''
        Required for use of sum() function. This
        will add histogramsa cross sample borders
        to be used in plotting.
        '''
        if other == 0:
            return Histogram(self.name, self.h.copy(), '___DUMMY___', self.region, self.rescale)
        else:
            return self.__add__(other)

    def __repr__(self):
        return f'{self.name}__{self.sample}__{self.region}__{self.rescale}'

    def __str__(self):
            return f'Hist: {self.name}, Sample: {self.sample}, Region: {self.region}, Rescale: {self.rescale}'

    def rebin(self, new_edges):
        # Need to match storage of incoming histogram
        histo = self.h
        new_axis = hist.axis.Variable(new_edges, name=histo.axes[0].name)
        hnew = hist.Hist.new.Var(new_edges, name=histo.axes[0].name, label=histo.label, flow=True).Weight()
        new_edges = new_axis.edges
        sw =  np.array(histo.values())
        sw2 =  np.array(histo.variances())

        edges_correct = []
        for ne in new_edges:
            available = False
            for oe in histo.axes[0].edges:
                if math.isclose(ne, oe, rel_tol = 1e-4):
                    available = True
            edges_correct.append(available)

        assert all(edges_correct)
        binmap = np.digitize(histo.axes[0].centers, new_edges)
        new_sw, new_sw2 = [], []

        for bin_num in sorted(set(binmap)):
            old_bins_in_this_bin = np.where(binmap == bin_num)[0]
            w_slice = sw[old_bins_in_this_bin].sum()
            sw2_slice = sw2[old_bins_in_this_bin].sum()
            new_sw.append(w_slice)
            new_sw2.append(sw2_slice)
        hnew[...] = np.stack([new_sw, new_sw2], axis=-1)

        self.h = hnew

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

    def __getitem__(self, histo):

        if isinstance(histo, Histogram):
            key = (histo.name, histo.sample, histo.region, histo.rescale)
        else:
            key = histo
        return self.to_plot[key]

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
