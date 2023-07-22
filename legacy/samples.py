from classes import *

## Weights
def MC_weight(xsec_weight, weight_mc,weight_pileup, weight_bTagSF_DL1r_Continuous,weight_jvt,weight_forwardjvt,weight_leptonSF, runNumber,totalEventsWeighted):
    return (36646.74*(runNumber<290000)+44630.6*((runNumber>=290000) & (runNumber<310000))+58791.6*(runNumber>=310000))*weight_mc*xsec_weight*weight_pileup*weight_bTagSF_DL1r_Continuous*weight_jvt*weight_forwardjvt*weight_leptonSF/totalEventsWeighted

def MM_weight(mm_weight):
    return mm_weight[:, 0]

mc_weight = Functor(MC_weight, ['xsec_weight','weight_mc','weight_pileup','weight_bTagSF_DL1r_Continuous','weight_jvt','weight_forwardjvt','weight_leptonSF','runNumber','totalEventsWeighted'])
mm_weight = Functor(MM_weight, ['mm_weight'])


# Selection
tight_lepton = lambda lepton_tight: lepton_tight[:,0] == 1
xxx_is_c     = lambda HFClass: HFClass == -1
xxx_is_b     = lambda HFClass: HFClass == 1
xxx_is_light = lambda HFClass: HFClass == 0

xxx_is_2b    = lambda HFClass: ( (abs(HFClass) >= 200) & (abs(HFClass) < 1000) ) | ( (abs(HFClass) >= 1100) & (abs(HFClass) < 2000) ) | (abs(HFClass) >= 2000)
xxx_is_1b    = lambda HFClass: ( (abs(HFClass) >= 1000) & (abs(HFClass) < 1100) ) | ( (abs(HFClass) >= 100) & (abs(HFClass) < 200) ) | (abs(HFClass) < 200)

leptight_cut = Functor(tight_lepton, ['leptons_PLIVtight'])
ttb_cut = Functor( lambda x, y: (tight_lepton(x)) & (xxx_is_b(y)),     ['leptons_PLIVtight','HF_SimpleClassification'])
ttc_cut = Functor( lambda x, y: (tight_lepton(x)) & (xxx_is_c(y)),     ['leptons_PLIVtight','HF_SimpleClassification'])
ttl_cut = Functor( lambda x, y: (tight_lepton(x)) & (xxx_is_light(y)), ['leptons_PLIVtight','HF_SimpleClassification'])

ttbb_cut = Functor( lambda x, y: (tight_lepton(x)) & (xxx_is_2b(y)), ['leptons_PLIVtight','HF_Classification'])
tt1b_cut = Functor( lambda x, y: (tight_lepton(x)) & (xxx_is_1b(y)), ['leptons_PLIVtight','HF_Classification'])

samples = [

    Sample('tH',
           'SIG',
           ['346676*'],
           leptight_cut,
           mc_weight,
           '#e6194b',
           'tHjb'),

    # Sample('tWH',
    #         'BKG',
    #        ['346678*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#3cb44b',
    #        'tWH'),

    # Sample('ttb_hdamp_m3top',
    #        'BKG',
    #        ['410480_AFII*','410482_AFII*'],
    #        ttb_cut,
    #        mc_weight,
    #        '#e6194b',
    #        r'$t\bar{t}+\geq1b$ (hdamp)'),

    Sample('ttb',
           'BKG',
           ['410470_user*'],
           ttb_cut,
           mc_weight,
           '#e6beff',
           r'$t\bar{t}+\geq1b$',
           UseAsRef=True),

    # Sample('ttb_AFII',
    #        'BKG',
    #        ['410470_AFII*'],
    #        ttb_cut,
    #        mc_weight,
    #        '#e6beff',
    #        r'$t\bar{t}+\geq1b$ (AFII)'),

    # Sample('ttb_4FS',
    #        'BKG',
    #        ['411180_AFII*','411179_AFII*','411178_AFII*'],
    #        ttb_cut,
    #        mc_weight,
    #        '#e6beff',
    #        r'$t\bar{t}+\geq1b$ (4FS)'),

    # Sample('ttb_4FS_2b',
    #        'BKG',
    #        ['411180_AFII*','411179_AFII*','411178_AFII*'],
    #        ttbb_cut,
    #        mc_weight,
    #        '#000075',
    #        r'$t\bar{t}+2b$ (4FS)'),

    Sample('ttb_4FS_1bB',
           'BKG',
           ['411180_AFII*','411179_AFII*','411178_AFII*'],
           tt1b_cut,
           mc_weight,
           'orange',
           r'$t\bar{t}+1b/B$ (4FS)'),

    # Sample('ttb_2b',
    #        'BKG',
    #        ['410470_user*'],
    #        ttbb_cut,
    #        mc_weight,
    #        'green', #'#000075',
    #        r'$t\bar{t}+2b$ (5FS)'),

    Sample('ttb_1bB',
           'BKG',
           ['410470_user*'],
           tt1b_cut,
           mc_weight,
           'green', #'orange',
           r'$t\bar{t}+1b/B$ (5FS)'),

    # Sample('ttc',
    #         'BKG',
    #        ['410470_user*'],
    #        ttc_cut,
    #        mc_weight,
    #        '#000075',
    #        r'$t\bar{t}+\geq1c$'),

    # # Sample('ttlight',
    #           'BKG',
    #        ['410470_user*'],
    #        ttl_cut,
    #        mc_weight,
    #        '#4363d8',
    #        r'$t\bar{t}+\geq0l$'),

    # Sample('ttlight_AFII',
    #         'BKG',
    #        ['410470_AFII*'],
    #        ttl_cut,
    #        mc_weight,
    #        '#000075',
    #        r'$t\bar{t}+\geq0l$ (AFII)',
    #        UseAsRef=True),

    # Sample('ttlight_aMCH7',
    #           'BKG',
    #        ['412116_AFII*', '412117_AFII*'],
    #        ttl_cut,
    #        mc_weight,
    #        '#3cb44b',
    #        r'$t\bar{t}+\geq0l$ (aMC@H7)'),

    # Sample('ttlight_PH7',
    #         'BKG',
    #        ['411233_AFII*', '411234_AFII*'],
    #        ttl_cut,
    #        mc_weight,
    #        '#911eb4',
    #        r'$t\bar{t}+\geq0l$ (Pow@H7)'),

    # Sample('ttH',
    #         'BKG',
    #        ['346343_user*', '346344_user*', '346345_user*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#911eb4',
    #        r'$t\bar{t}+H$'),

    # Sample('ttZ',
    #         'BKG',
    #        ['410156_user*', '410157_user*', '410218_user*', '410219_user*', '410220_user*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#46f0f0',
    #        r'$t\bar{t}+Z$'),

    # Sample('ttW',
    #         'BKG',
    #        ['412123_user*', '410155_user*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#f032e6',
    #        r'$t\bar{t}+W$'),

    # Sample('tZq',
    #         'BKG',
    #        ['410560_user*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#bcf60c',
    #        'tZq'),

    # Sample('tWZ',
    #         'BKG',
    #        ['410408*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#fabebe',
    #        'tWZ'),

    # Sample('singletop_Wtchannel',
    #         'BKG',
    #        ['410646_user*', '410647_user*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#008080',
    #        't (s-chan)'),

    # Sample('singletop_tchan',
    #        'BKG',
    #        ['410658_user*', '410659_user*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#f58231',
    #        't (t-chan)'),

    # Sample('singletop_schannel',
    #         'BKG',
    #        ['410644_user*', '410645_user*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#9a6324',
    #        'tW'),

    # Sample('Wjets',
    #         'BKG',
    #        ['364156*', '364159*', '364162*', '364165*', '364170*', '364173*', '364176*', '364179*', '364184*', '364187*', '364190*', '364193*', '364157*', '364160*', '364163*', '364166*', '364171*', '364174*', '364177*', '364180*', '364185*', '364188*', '364191*', '364194*', '364158*', '364161*', '364164*', '364167*', '364172*', '364175*', '364178*', '364181*', '364186*', '364189*', '364192*', '364195*', '364168*', '364169*', '364182*', '364183*', '364196*', '364197*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#fffac8',
    #        'W+jets'),

    # Sample('Zjets',
    #         'BKG',
    #        ['364100*', '364103*', '364106*', '364109*', '364114*', '364117*', '364120*', '364123*', '364128*', '364131*', '364134*', '364137*', '364101*', '364104*', '364107*', '364110*', '364115*', '364118*', '364121*', '364124*', '364129*', '364132*', '364135*', '364138*', '364102*', '364105*', '364108*', '364111*', '364116*', '364119*', '364122*', '364125*', '364130*', '364133*', '364136*', '364139*', '364112*', '364113*', '364126*', '364127*', '364140*', '364141*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#800000',
    #        'Z+jets'),

    # Sample('VV',
    #         'BKG',
    #        ['364250_user*', '364253_user*', '364254_user*', '364255_user*', '364288_user*', '364289_user*', '364290_user*', '363355_user*', '363356_user*', '363357_user*', '363358_user*', '363359_user*', '363360_user*', '363489_user*', '363494_user*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#aaffc3',
    #        'VV'),

    # Sample('otherHiggs',
    #         'BKG',
    #        ['342282*', '342283*', '342284*', '342285*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#808000',
    #        'Higgs'),

    # Sample('raretop',
    #         'BKG',
    #        ['304014*', '412043*'],
    #        leptight_cut,
    #        mc_weight,
    #        '#ffd8b1',
    #        'Rare Tops'),

    # Sample('Fakes',
    #         'BKG',
    #        ['data15*', 'data16*', 'data17*', 'data18*'],
    #        None,
    #        mm_weight,
    #        '#ffe119',
    #        'Fakes'),

    # Sample('Data',
    #        'DATA',
    #        ['data15*', 'data16*', 'data17*', 'data18*'],
    #        leptight_cut,
    #        None,
    #        '#808080',
    #        'Data'),
]


samples_list = Samples(samples)