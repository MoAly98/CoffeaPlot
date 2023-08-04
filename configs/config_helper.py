import awkward as ak

# ===== Weights ===== #

def MC_weight(xsec_weight, weight_mc,weight_pileup, weight_bTagSF_DL1r_Continuous,weight_jvt,weight_forwardjvt,weight_leptonSF, runNumber,totalEventsWeighted):
    return (36646.74*(runNumber<290000)+44630.6*((runNumber>=290000) & (runNumber<310000))+58791.6*(runNumber>=310000))*weight_mc*xsec_weight*weight_pileup*weight_bTagSF_DL1r_Continuous*weight_jvt*weight_forwardjvt*weight_leptonSF/totalEventsWeighted

def MM_weight(mm_weight):
    return mm_weight[:, 0]

# ==== Variables ==== #

bdt_tH  =  lambda x: x[:,0]
bdt_ttb = lambda x: x[:,1]
nlights = lambda njets, nbjets: njets - nbjets
tagnonb_topb_m = lambda tagnonb_topb_m: tagnonb_topb_m/1e3

# ===== Selection ===== #
# Selection
tight_lepton = lambda lepton_tight: lepton_tight[:,0] == 1
xxx_is_c     = lambda HFClass: HFClass == -1
xxx_is_b     = lambda HFClass: HFClass == 1
xxx_is_light = lambda HFClass: HFClass == 0
xxx_is_2b    = lambda HFClass: ( (abs(HFClass) >= 200) & (abs(HFClass) < 1000) ) | ( (abs(HFClass) >= 1100) & (abs(HFClass) < 2000) ) | (abs(HFClass) >= 2000)
xxx_is_1b    = lambda HFClass: ( (abs(HFClass) >= 1000) & (abs(HFClass) < 1100) ) | ( (abs(HFClass) >= 100) & (abs(HFClass) < 200) )

ttb_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_b(y))
ttc_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_c(y))
ttl_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_light(y))
ttbb_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_2b(y))
tt1b_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_1b(y))

# ===== Regions ===== #
# PRESEL
PR_fn     =    lambda njets, nbjets, njets_CBT4, njets_CBT5, nalljets, njets_CBT0, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0)
# SIGNAL REGIONS
SR_fn     =    lambda njets, nbjets, njets_CBT4, njets_CBT5, nalljets, njets_CBT0, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & ((nalljets - njets_CBT5 - njets_CBT4 - njets_CBT0) < 2) & (nfwd>0)
# TTB CR REGIONS
CR_ttb_fn =    lambda njets, nbjets, njets_CBT4, njets_CBT5, nalljets, njets_CBT0, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & ((nalljets - njets_CBT5 - njets_CBT4 - njets_CBT0) >= 2) & (nfwd==0)

# ===== Rescales ===== #

ttb_1p25_rescale = lambda w: w*1.25