from classes import *

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

samples_list = [

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


plot_samples = Samples(samples_list)