class Functor(object):
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
        assert isinstance(self.args, list)

    def evaluate(self, data):
        data_args = [data[arg] for arg in self.args]
        return self.fn(*data_args)