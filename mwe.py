


import os, re
from glob import glob
from coffea import processor
from coffea.nanoevents import  BaseSchema

def MC_weight(xsec_weight, weight_mc,weight_pileup, weight_bTagSF_DL1r_Continuous,weight_jvt,weight_forwardjvt,weight_leptonSF, runNumber,totalEventsWeighted, mm_weight0):
    return (36207.66*(runNumber<290000)+44307.4*((runNumber>=290000) & (runNumber<310000))+58450.1*(runNumber>=310000))*weight_mc*xsec_weight*weight_pileup*weight_bTagSF_DL1r_Continuous*weight_jvt*weight_forwardjvt*weight_leptonSF/totalEventsWeighted


class Functor(object):
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
        assert isinstance(self.args, list)

    def evaluate(self, data):
        data_args = [data[arg] for arg in self.args]
        return data[self.fn(*data_args)]

class Sample(object):
    def __init__(self, name, cut_howto, weight):
        self.name = name
        # Set sample cuts
        self.sel = cut_howto
        self.weight = weight


class MyProcessor(processor.ProcessorABC):
    def __init__(self):
        pass
    def process(self, presel_events):
        dataset = presel_events.metadata['dataset']
        for sample in plot_samples:
            if dataset == sample.name:
                current_sample = sample
                break
        filt_sample = sample.sel.evaluate(presel_events)
        return {dataset: 0}
    def postprocess(self, accumulator):
        pass

tight_lepton = lambda lepton_tight: lepton_tight[:,0] == 1
mc_weight = Functor(MC_weight, ['xsec_weight','weight_mc','weight_pileup','weight_bTagSF_DL1r_Continuous','weight_jvt','weight_forwardjvt','weight_leptonSF','runNumber','totalEventsWeighted'])

leptight_cut = Functor(tight_lepton, ['leptons_PLIVtight'])
plot_samples = [Sample('tH', leptight_cut, mc_weight,),]

if __name__ == '__main__':
    print("oK1")
    #plot_samples = plot_samples
    fileset = {'tH': glob('/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16a_nom/346676*.root')}
    tree = 'nominal_Loose'
    executor = processor.FuturesExecutor(workers=8)
    run = processor.Runner(executor=executor, metadata_cache={}, schema=BaseSchema)
    _ = run(fileset, tree, MyProcessor())