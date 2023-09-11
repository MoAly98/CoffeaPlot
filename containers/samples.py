import os, re
from glob import glob

class Sample(object):
    def __init__(self, name, stype = None, regexes = None, cut_howto = None, mc_weight = None, weight_howto = None, ignore_mcweight = None, color = None, label = None, category = None, UseAsRef = False, direcs = None):

        # Sample name
        self.name = name

        self.type = stype.upper()
        # Get files for sample
        self.regexes = regexes
        self.direcs = direcs
        self.files = []

        # Set sample cuts
        self.sel = cut_howto

        # Set sample weight
        self.weight = weight_howto
        self.mc_weight = mc_weight

        # Sample color
        self.color = color

        # Sample label
        self.label = label

        # Sample category
        self.category = category

        # Should this sample be used as reference MC?
        self.ref = UseAsRef

        # Is this a super sample
        self.is_super = False


    def create_fileset(self):

        if self.regexes is None:
            return []
        # Collect Regexes
        to_glob = []
        for direc in self.direcs:
            to_glob.extend([f'{direc}/{regex}.root' for regex in self.regexes])

        # Collect files
        globbed   = []
        for wild in to_glob:
            globbed.extend(glob(wild))

        self.files = globbed
        assert self.files != [], f'NO files found for sample {self.name} with any regexes: {self.regexes} in any of the directories: {self.direcs}'


    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        sample_str = f"Sample: {self.name} \n Type: {self.type} \n Category: {self.category} \n Files: {self.regexes} \n Selection: {self.sel} \n Weight: {self.weight} \n MC Weight: {self.mc_weight} \n Color: {self.color} \n Label: {self.label} \n Use as reference MC: {self.ref}"

    def __hash__(self):
            return hash(self.name)

class SuperSample(Sample):

    def __init__(self, name, subsamples = None, regexes = None, direcs = None):

        self.name = name
        if subsamples is None:
            subsamples = []
        self.subsamples = subsamples
        # Get files for sample
        self.regexes = regexes
        self.direcs = direcs
        self.files = []
        self.is_super = True

    def add_subsample(self, subsample):
        self.subsamples.append(subsample)

    def __len__(self):
        return len(self.subsamples)