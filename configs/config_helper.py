import awkward as ak

# ===== Weights ===== #

def MC_weight(xsec_weight, weight_mc,weight_pileup, weight_bTagSF_DL1r_Continuous,weight_jvt,weight_forwardjvt,weight_leptonSF, runNumber,totalEventsWeighted):
    return (36646.74*(runNumber<290000)+44630.6*((runNumber>=290000) & (runNumber<310000))+58791.6*(runNumber>=310000))*weight_mc*xsec_weight*weight_pileup*weight_bTagSF_DL1r_Continuous*weight_jvt*weight_forwardjvt*weight_leptonSF/totalEventsWeighted

def MM_weight(mm_weight):
    return mm_weight[:, 0]

# ==== Variables ==== #

bdt_tH  =  lambda x: x[:,0]
bdt_ttb =  lambda x: x[:,1]
bdt_ttc =  lambda x: x[:,2]
bdt_ttl =  lambda x: x[:,3]
bdt_others = lambda x: x[:,4]

nlights = lambda njets, nbjets: njets - nbjets

x_gev  = lambda x: x/1e3

def obj0_x(x):
    x = ak.pad_none(x, 1, axis=1)
    x = ak.fill_none(x, -999, axis=1)
    return x[:,0]

def obj1_x(x):
    x = ak.pad_none(x, 2, axis=1)
    x = ak.fill_none(x, -999, axis=1)
    return x[:,1]

def obj2_x(x):
    x = ak.pad_none(x, 3, axis=1)
    x = ak.fill_none(x, -999, axis=1)
    return x[:,2]

def obj0_x_gev(x):
    x = ak.pad_none(x, 1, axis=1)
    x = ak.fill_none(x, -999, axis=1)
    return x[:,0]/1e3

def obj1_x_gev(x):
    x = ak.pad_none(x, 2, axis=1)
    x = ak.fill_none(x, -999, axis=1)
    return x[:,1]/1e3

def obj2_x_gev(x):
    x = ak.pad_none(x, 3, axis=1)
    x = ak.fill_none(x, -999, axis=1)
    return x[:,2]/1e3


obj0_x_GeV = lambda x:  x[:,0]/1e3
obj1_x_GeV = lambda x:  x[:,1]/1e3
obj2_x_GeV = lambda x:  x[:,2]/1e3

flatten_x = lambda x: ak.flatten(x)
flatten_x_gev = lambda x: ak.flatten(x/1e3)


def good_jets(pt, eta, truthflavExt, truthFlav, pcbt, dl1r):
    good_jets = (pt > 25e3) & (abs(eta) < 2.5)
    jets = ak.zip({
        'pt':                ak.where(good_jets, pt, [-999]),
        'eta':               ak.where(good_jets, eta, [-999]),
        'truthflavExt':      ak.where(good_jets, truthflavExt, [-999]),
        'truthFlav':         ak.where(good_jets, truthFlav, [-999]),
        'pcbt':              ak.where(good_jets, pcbt, [-999]),
        'DL1r':              ak.where(good_jets, dl1r, [-999]),
    })

    return jets

get_pt           = lambda x: x.pt
get_eta          = lambda x: x.eta
get_truthFlavExt = lambda x: x.truthflavExt
get_truthFlav    = lambda x: x.truthFlav
get_pcbt         = lambda x: x.pcbt
get_dl1r         = lambda x: x.DL1r


# ====== Efficiency ====== #

def b_70_pass(jets_truthFlav, jets_tagWeightBin_DL1r_Continuous):
    truthflav = ak.flatten(jets_truthFlav)
    pcbt = ak.flatten(jets_tagWeightBin_DL1r_Continuous)
    return (abs(truthflav) == 5) & (pcbt >= 4)

def b_70_pass_FixedCut(jets_truthFlav, jets_DL1r):
    try:
        truthflav = ak.flatten(jets_truthFlav)
        dl1r      = ak.flatten(jets_DL1r)
    except ValueError:
        truthflav = jets_truthFlav
        dl1r      = jets_DL1r
    return (abs(truthflav) == 5) & (dl1r >=  2.98 )

def c_70_pass(jets_truthFlav, jets_tagWeightBin_DL1r_Continuous):
    truthflav = ak.flatten(jets_truthFlav)
    pcbt = ak.flatten(jets_tagWeightBin_DL1r_Continuous)
    return (abs(truthflav) == 4) & (pcbt >= 4)

def light_70_pass(jets_truthFlav, jets_tagWeightBin_DL1r_Continuous):
    truthflav = ak.flatten(jets_truthFlav)
    pcbt = ak.flatten(jets_tagWeightBin_DL1r_Continuous)
    return (abs(truthflav) != 4 & abs(truthflav) != 5) & (pcbt >= 4)

def b_truth(jets_truthFlav):
    try:
        truthflav = ak.flatten(jets_truthFlav)
    except ValueError:
        truthflav = jets_truthFlav

    return (abs(truthflav) == 5)

def c_truth(jets_truthFlav):
    truthflav = ak.flatten(jets_truthFlav)
    return (abs(truthflav) == 4)

def light_truth(jets_truthFlav):
    truthflav = ak.flatten(jets_truthFlav)
    return (abs(truthflav) != 4 & abs(truthflav) != 5)

# ===== Selection ===== #
# Selection
tight_lepton = lambda lepton_tight: lepton_tight[:,0] == 1
xxx_is_c     = lambda HFClass: HFClass == -1
xxx_is_b     = lambda HFClass: HFClass == 1
xxx_is_light = lambda HFClass: HFClass == 0

xxx_is_2b    = lambda HFClass: ( (abs(HFClass) >= 200) & (abs(HFClass) < 1000) ) | ( (abs(HFClass) >= 1100) & (abs(HFClass) < 2000) ) | (abs(HFClass) >= 2000)
xxx_is_1b    = lambda HFClass: ( (abs(HFClass) >= 1000) & (abs(HFClass) < 1100) )
xxx_is_1B    = lambda HFClass: ( (abs(HFClass) >= 100)  & (abs(HFClass) < 200) )
xxx_is_1bB    = lambda HFClass: (( xxx_is_1b(HFClass) ) | ( xxx_is_1B(HFClass) ))

xxx_is_1c    = lambda HFClass: ( (abs(HFClass)  >= 10) & (abs(HFClass) < 11) )
xxx_is_2c    = lambda HFClass: ( ((abs(HFClass) >= 20) & (abs(HFClass) < 100)) | ((abs(HFClass) >= 2) & (abs(HFClass) < 10)) | ((abs(HFClass) >= 11 ) & (abs(HFClass) < 20))) # 2*n*c + 0b +0C | 2*n*C + 0b + 0c | 1c1C + 0b
xxx_is_1C    = lambda HFClass: ( (abs(HFClass)  >= 1) & (abs(HFClass) < 2) )

ttb_cut   = lambda x, y: (tight_lepton(x)) & (xxx_is_b(y))
ttc_cut   = lambda x, y: (tight_lepton(x)) & (xxx_is_c(y))
ttl_cut   = lambda x, y: (tight_lepton(x)) & (xxx_is_light(y))
ttbb_cut  = lambda x, y: (tight_lepton(x)) & (xxx_is_2b(y))
tt1b_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_1b(y))
tt1B_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_1B(y))
tt1bB_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_1bB(y))

ttcc_cut  = lambda x, y: (tight_lepton(x)) & (xxx_is_2c(y))
tt1c_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_1c(y))
tt1C_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_1C(y))

def at_least_a_jet(jets_pt):

    return ak.count(jets_pt, axis = 1) > 0

# ===== Regions ===== #
#Inclusive

def INCL_fn(el_Id_TightLH, el_Isol_PLImprovedTight, mu_Id_Medium, mu_Isol_PLImprovedTight, jets_pt):

    lepton_id = ak.where(ak.num(el_Id_TightLH, axis=1) > 0, el_Id_TightLH, mu_Id_Medium)
    lepton_iso = ak.where(ak.num(el_Isol_PLImprovedTight, axis=1) > 0, el_Isol_PLImprovedTight, mu_Isol_PLImprovedTight)
    lepton_plivtight = lepton_id*lepton_iso

    return lepton_plivtight[:,0] == 1


# PRESEL
PR_fn     =    lambda njets, nbjets, njets_CBT4, njets_CBT5, nalljets, njets_CBT0, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0)
# SIGNAL REGIONS
SR_fn     =    lambda njets, nbjets, njets_CBT4, njets_CBT5, nalljets, njets_CBT0, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & ((nalljets - njets_CBT5 - njets_CBT4 - njets_CBT0) <  2) & (nfwd>0)
# TTB CR REGIONS
CR_ttb_fn =    lambda njets, nbjets, njets_CBT4, njets_CBT5, nalljets, njets_CBT0, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & ((nalljets - njets_CBT5 - njets_CBT4 - njets_CBT0) >= 2) & (nfwd==0)
# NO BTAG PRESEL
# PR_NO_BTAG_fn     =    lambda njets, nbjets, njets_CBT4, njets_CBT5, nalljets, njets_CBT0, tau_pt, nfwd:  (ak.num(tau_pt, axis=1) == 0) &

# ===== Rescales ===== #

ttb_1p25_rescale = lambda w: w*1.25