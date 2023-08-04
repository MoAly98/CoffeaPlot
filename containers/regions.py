class Region(object):
    def __init__(self, name, howto, target_sample = [], label = None):
        self.name = name
        self.sel = howto
        self.targets = target_sample
        self.label = label

    def __eq__(self, other):
        return self.name == other.name
