import awkward as ak
from coffea import processor
import coffea
#from coffea.hist import plotratio
from coffea.nanoevents import  BaseSchema
import hist

from collections import defaultdict
import matplotlib.pyplot as plt
import uproot
import mplhep as hep
import numpy as np
import pandas as pd
#import seaborn as sns
#os.environ["MALLOC_TRIM_THRESHOLD_"] = "65536"


#from classes import *
#from  samples import *
#from regions import *
#from rescalings import *
#from variables import *

import os, re
from glob import glob

LOOK_IN = ['/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16a_nom/',
           '/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16d_nom/',
           '/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16e_nom/',
           '/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v0/data_nom/'
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
        self.to_plot = to_plot
    def append(self, plot_histo):
        self.to_plot.append(plot_histo)

class Plot(object):
    def __init__(self, name, howto, binning, label, regions=None, idx_by = 'event'):
        self.name = name
        self.howto = howto
        self.binning = binning
        self.label = label
        self.regions = regions
        self.idx = idx_by
        assert self.idx in ['event','nonevent']

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

class MyProcessor(processor.ProcessorABC):

    def __init__(self, plots_list, columns=[]):
        self._columns = columns
        self.plots_list = plots_list

    @property
    def columns(self):
        return self._columns

    def dd(self):
        return defaultdict(dict)

    def process(self, presel_events):

        output_1d = defaultdict(self.dd)
        output_2d = defaultdict(self.dd)
        dataset = presel_events.metadata['dataset']

        for a_sample in plot_samples:
            if dataset != a_sample.name: continue

            sample = a_sample
            break

        #affecting_rescales = [rescale for rescale in plot_rescales if sample.name in rescale.affect ] + [ Rescales('ProtNominal', [sample.name], Functor(lambda w: w, ['weights']) ) ]

        sample_weights = sample.weight.evaluate(presel_events) if sample.weight is not None else 1.0

        presel_events['weights'] = sample_weights
        filt_sample = presel_events[sample.sel.evaluate(presel_events)] if sample.sel is not None else presel_events

        # ====== Loop over 1D plots ====== #

        for plot in self.plots_list.to_plot:
            name          = plot.name
            region_to_use = plot.regions
            idxing        = plot.idx
            binning       = plot.binning
            label         = plot.label
            histo_compute = howto

            for region_to_plot in plot_regions:

                if re.match(region_to_use, region) is None and region_to_use != 'all': return 0

                filt_reg = filt_sample[region.sel.evaluate(filt_sample)]

                if plots_list.dim == 1:
                    h = hist.Hist.new.Var(binning, name = label, label=label, flow=True).Weight()
                else:
                    # TODO:: 2D
                    pass

                # ================ Empty histogram for this region for this sample ===========
                if ak.num(filt_reg['weights'], axis=0) == 0:
                    for scaling in affecting_rescales:
                        output_1d[region][scaling.name][name] = hist.Hist.new.Var(binning, name = label, label=label, flow=True).Weight()
                        output_2d[region][scaling.name][name] = None # Need empty 2D histo here

                    return 0

                # =============== Non empty histogram for this region for this sample ==========

                if plots_list.dim == 1:

                    for scaling in affecting_rescales:
                        rescaled_weights = scaling.method.evaluate(filt_reg)

                        if idxing == 'nonevent':
                            assert len(plot.howto.args) == 1, "Composite variables are not supported when indexing by nonevent"

                            w, arg = ak.broadcast_arrays(rescaled_weights[:, np.newaxis], filt_reg[histo_compute.args[0]])
                            data = histo_compute.fn(arg)
                            w = ak.flatten(w)
                        else:
                            data = histo_compute.evaluate(filt_reg)
                            w = rescaled_weights

                        # Fill the histogram
                        h.fill(data, weight = w)

                        # Save the histogram
                        output_1d[region][scaling.name][name] = h


                else:
                    # TODO:: 2D
                    pass


        return {dataset: {'1D': output_1d, '2D': output_2d}}

    def postprocess(self, accumulator):
        pass

## Weights
def MC_weight(xsec_weight, weight_mc,weight_pileup, weight_bTagSF_DL1r_Continuous,weight_jvt,weight_forwardjvt,weight_leptonSF, runNumber,totalEventsWeighted):
    return (36207.66*(runNumber<290000)+44307.4*((runNumber>=290000) & (runNumber<310000))+58450.1*(runNumber>=310000))*weight_mc*xsec_weight*weight_pileup*weight_bTagSF_DL1r_Continuous*weight_jvt*weight_forwardjvt*weight_leptonSF/totalEventsWeighted

def MM_weight(mm_weight):
    return mm_weight[:, 0]

mc_weight = Functor(MC_weight, ['xsec_weight','weight_mc','weight_pileup','weight_bTagSF_DL1r_Continuous','weight_jvt','weight_forwardjvt','weight_leptonSF','runNumber','totalEventsWeighted'])
mm_weight = Functor(MM_weight, ['mm_weight'])


# Selection
tight_lepton = lambda lepton_tight: lepton_tight[:,0] == 1
xxx_is_c     = lambda HFClass: HFClass == -1
xxx_is_b     = lambda HFClass: HFClass == 1
xxx_is_light = lambda HFClass: HFClass == 0


leptight_cut = Functor(tight_lepton, ['leptons_PLIVtight'])
ttb_cut = Functor( lambda x, y: (tight_lepton(x)) & (xxx_is_b(y)),     ['leptons_PLIVtight','HF_SimpleClassification'])
ttc_cut = Functor( lambda x, y: (tight_lepton(x)) & (xxx_is_c(y)),     ['leptons_PLIVtight','HF_SimpleClassification'])
ttl_cut = Functor( lambda x, y: (tight_lepton(x)) & (xxx_is_light(y)), ['leptons_PLIVtight','HF_SimpleClassification'])

plot_samples = [

    Sample('tH',
            ['346676*'],
           leptight_cut,
           mc_weight,
           '#e6194b',
           'tHjb'),

    Sample('tWH',
           ['346678*'],
           leptight_cut,
           mc_weight,
           '#3cb44b',
           'tWH'),

    Sample('ttb',
           ['410470_user*'],
           ttb_cut,
           mc_weight,
           '#ffe119',
           r'$t\bar{t}+\geq1b$'),

    Sample('ttc',
           ['410470_user*'],
           ttc_cut,
           mc_weight,
           '#4363d8',
           r'$t\bar{t}+\geq1c$'),

    Sample('ttlight',
           ['410470_user*'],
           ttl_cut,
           mc_weight,
           '#f58231',
           r'$t\bar{t}+\geq0l$'),

    Sample('ttH',
           ['346343_user*', '346344_user*', '346345_user*'],
           leptight_cut,
           mc_weight,
           '#911eb4',
           r'$t\bar{t}+H$'),

    Sample('ttZ',
           ['410156_user*', '410157_user*', '410218_user*', '410219_user*', '410220_user*'],
           leptight_cut,
           mc_weight,
           '#46f0f0',
           r'$t\bar{t}+Z$'),

    Sample('ttW',
           ['412123_user*', '410155_user*'],
           leptight_cut,
           mc_weight,
           '#f032e6',
           r'$t\bar{t}+W$'),

    Sample('tZq',
           ['410560_user*'],
           leptight_cut,
           mc_weight,
           '#bcf60c',
           'tZq'),

    Sample('tWZ',
           ['410408*'],
           leptight_cut,
           mc_weight,
           '#fabebe',
           'tWZ'),
    Sample('singletop_Wtchannel',
           ['410646_user*', '410647_user*'],
           leptight_cut,
           mc_weight,
           '#008080',
           't (s-chan)'),
    Sample('singletop_tchan',
           ['410658_user*', '410659_user*'],
           leptight_cut,
           mc_weight,
           '#e6beff',
           't (t-chan)'),

    Sample('singletop_schannel',
           ['410644_user*', '410645_user*'],
           leptight_cut,
           mc_weight,
           '#9a6324',
           'tW'),

    Sample('Wjets',
           ['364156*', '364159*', '364162*', '364165*', '364170*', '364173*', '364176*', '364179*', '364184*', '364187*', '364190*', '364193*', '364157*', '364160*', '364163*', '364166*', '364171*', '364174*', '364177*', '364180*', '364185*', '364188*', '364191*', '364194*', '364158*', '364161*', '364164*', '364167*', '364172*', '364175*', '364178*', '364181*', '364186*', '364189*', '364192*', '364195*', '364168*', '364169*', '364182*', '364183*', '364196*', '364197*'],
           leptight_cut,
           mc_weight,
           '#fffac8',
           'W+jets'),

    Sample('Zjets',
           ['364100*', '364103*', '364106*', '364109*', '364114*', '364117*', '364120*', '364123*', '364128*', '364131*', '364134*', '364137*', '364101*', '364104*', '364107*', '364110*', '364115*', '364118*', '364121*', '364124*', '364129*', '364132*', '364135*', '364138*', '364102*', '364105*', '364108*', '364111*', '364116*', '364119*', '364122*', '364125*', '364130*', '364133*', '364136*', '364139*', '364112*', '364113*', '364126*', '364127*', '364140*', '364141*'],
           leptight_cut,
           mc_weight,
           '#800000',
           'Z+jets'),

    Sample('VV',
           ['364250_user*', '364253_user*', '364254_user*', '364255_user*', '364288_user*', '364289_user*', '364290_user*', '363355_user*', '363356_user*', '363357_user*', '363358_user*', '363359_user*', '363360_user*', '363489_user*', '363494_user*'],
           leptight_cut,
           mc_weight,
           '#aaffc3',
           'VV'),

    Sample('otherHiggs',
           ['342282*', '342283*', '342284*', '342285*'],
           leptight_cut,
           mc_weight,
           '#808000',
           'Higgs'),

    Sample('raretop',
           ['304014*', '412043*'],
           leptight_cut,
           mc_weight,
           '#ffd8b1',
           'Rare Tops'),

    Sample('Fakes',
           ['data15*', 'data16*', 'data17*', 'data18*'],
           None,
           mm_weight,
           '#000075',
           'Fakes'),

    Sample('Data',
           ['data15*', 'data16*', 'data17*', 'data18*'],
           leptight_cut,
           None,
           '#808080',
           'Data'),
]


# PRESEL
PR_fn =    lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0)
# SIGNAL REGIONS
SR_fn    =  lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & (njets_CBT123 < 2) & (nfwd>0)
# TTB CR REGIONS
CR_ttb_fn        = lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & (njets_CBT123 >= 2) & (nfwd==0)

plot_regions = [

    Region('PR', Functor(PR_fn, ['njets','nbjets','njets_CBT4', 'njets_CBT5', 'njets_CBT123', 'tau_pt','nfwdjets'])),
    Region('SR', Functor(SR_fn, ['njets','nbjets','njets_CBT4', 'njets_CBT5', 'njets_CBT123', 'tau_pt','nfwdjets'])),
    Region('CR', Functor(CR_ttb_fn, ['njets','nbjets','njets_CBT4', 'njets_CBT5', 'njets_CBT123', 'tau_pt','nfwdjets'])),

]

plot_rescales = [
    Rescales('ttb_1p25',['ttb'], Functor(lambda w: w*1.25, ['weights'])),
]

plots_to_make = []

plot_list_1D = [
    Plot('new_bdt_tH', Functor(lambda x: x[:,0], ['BDT']), [0, 0.3528, 0.6, 0.78, 1],   'NewBDT(tH)'),

    Plot('alt_bdt_tH',Functor(lambda x: x[:,0], ['BDT_alt']), [0, 0.346, 0.593, 0.786, 1], 'AltBDT(tH)'),

    Plot('new_bdt_ttb',Functor(lambda x: x[:,1], ['BDT']), [0,0.2,0.3,0.4,0.5,1.0],     'NewBDT(ttb)'),

    Plot('alt_bdt_ttb',Functor(lambda x: x[:,1], ['BDT_alt']), [0,0.2,0.3,0.4,0.5,1.0],     'AltBDT(ttb)'),
]

plots_1d_nom = Plots(1, 'nominal_Loose', plot_list_1D)
plots_to_make.append(plots_1d_nom)

plots_2d_nom = Plots(2, 'nominal_Loose')
plots_to_make.append(plots_2d_nom)

if __name__ == '__main__':

    #fileset = {'tH': glob('/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16a_nom/346676*.root') + glob('/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16d_nom/346676*.root') + glob('/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/tH_v34_minintuples_v3/mc16e_nom/346676*.root')}
    fileset = {}
    for sample in plot_samples:
        fileset[sample.name] = sample.files

    tree_to_plot_list = {}
    for plots_list in plots_to_make:
        tree_to_plot_list[plots_list.tree] = plots_list

    #executor = processor.FuturesExecutor(workers=8)
    executor = processor.IterativeExecutor()
    for tree, plots_list in tree_to_plot_list.items():

        run = processor.Runner(executor=executor, metadata_cache={}, schema=BaseSchema, skipbadfiles=True)
        _ = run(fileset, tree, MyProcessor(plots_list))

        print(_)