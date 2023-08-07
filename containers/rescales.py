from containers.functors import Functor

class Rescale(object):
    def __init__(self, name, affected_samples_names, howto, label = None):
        self.name   = name
        self.affects = affected_samples_names
        self.method = howto
        assert isinstance(self.method, Functor), "Rescale howto must be a functor"
        assert 'weights' in self.method.args, "A branch called weights must be in data and passed to functor for rescaling"

        self.label = label

    def __eq__(self, other):
        return self.name == other.name