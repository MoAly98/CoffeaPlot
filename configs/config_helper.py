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
obj0_x = lambda x: x[:,0]
obj1_x = lambda x: x[:,1]
obj2_x = lambda x: x[:,2]

flatten_x = lambda x: ak.flatten(x)
flatten_x_gev = lambda x: ak.flatten(x/1e3)

# ====== Efficiency ====== #

def b_70_pass(jets_truthFlav, jets_tagWeightBin_DL1r_Continuous):
    truthflav = ak.flatten(jets_truthFlav)
    pcbt = ak.flatten(jets_tagWeightBin_DL1r_Continuous)
    return (abs(truthflav) == 5) & (pcbt >= 4)

def c_70_pass(jets_truthFlav, jets_tagWeightBin_DL1r_Continuous):
    truthflav = ak.flatten(jets_truthFlav)
    pcbt = ak.flatten(jets_tagWeightBin_DL1r_Continuous)
    return (abs(truthflav) == 4) & (pcbt >= 4)

def light_70_pass(jets_truthFlav, jets_tagWeightBin_DL1r_Continuous):
    truthflav = ak.flatten(jets_truthFlav)
    pcbt = ak.flatten(jets_tagWeightBin_DL1r_Continuous)
    return (abs(truthflav) != 4 & abs(truthflav) != 5) & (pcbt >= 4)

def b_truth(jets_truthFlav):
    truthflav = ak.flatten(jets_truthFlav)
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


# ===== Regions ===== #
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