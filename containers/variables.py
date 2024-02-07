class Variable(object):

    def __init__(self, name, howto, binning, label, regions=['.*'], idx_by = 'event', dim = None, vtype = None, rebin = None, nice_vals=None):
        self.name = name
        self.howto = howto
        self.binning = binning
        self.label = label
        self.regions = regions
        self.idx = idx_by
        assert self.idx in ['event','nonevent']

        self.dim = dim
        assert self.dim in [1,2]

        self.rebin = rebin

        self.nice_vals = nice_vals
        self.type = vtype

    def set_dim(self, dim):
        self.dim = dim

    def __eq__(self, other):
        return self.name == other.name

class Eff(Variable):
    def __init__(self, name, howto, numsel, denomsel, binning, label, regions=['.*'], idx_by = 'event', dim = None, vtype = None, rebin = None):
        self.numsel = numsel
        self.denomsel = denomsel
        Variable.__init__(self, name, howto, binning, label, regions=regions, idx_by = idx_by, dim = dim, rebin = rebin)

class Variables(object):
    def __init__(self, dim, tree, to_plot = []):
        if dim != 1 and dim != 2:
            print("ERROR:: Supporting only 1D and 2D variables")
            exit()
        self.dim = dim
        self.tree = tree
        for variable in to_plot:
            variable.set_dim(self.dim)
        self.type = vtype

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