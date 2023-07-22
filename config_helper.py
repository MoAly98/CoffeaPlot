from classes import Functor
import awkward as ak

# ===== Weights ===== #

def MC_weight(xsec_weight, weight_mc,weight_pileup, weight_bTagSF_DL1r_Continuous,weight_jvt,weight_forwardjvt,weight_leptonSF, runNumber,totalEventsWeighted):
    return (36646.74*(runNumber<290000)+44630.6*((runNumber>=290000) & (runNumber<310000))+58791.6*(runNumber>=310000))*weight_mc*xsec_weight*weight_pileup*weight_bTagSF_DL1r_Continuous*weight_jvt*weight_forwardjvt*weight_leptonSF/totalEventsWeighted

def MM_weight(mm_weight):
    return mm_weight[:, 0]

# ==== Variables ==== #

bdt_tH  =  lambda x: x[:,0]
bdt_ttb = lambda x: x[:,1]

# ===== Selection ===== #
# Selection
tight_lepton = lambda lepton_tight: lepton_tight[:,0] == 1
xxx_is_c     = lambda HFClass: HFClass == -1
xxx_is_b     = lambda HFClass: HFClass == 1
xxx_is_light = lambda HFClass: HFClass == 0

ttb_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_b(y))
ttc_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_c(y))
ttl_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_light(y))


# ===== Regions ===== #
# PRESEL
PR_fn     =    lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0)
# SIGNAL REGIONS
SR_fn     =    lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & (njets_CBT123 < 2) & (nfwd>0)
# TTB CR REGIONS
CR_ttb_fn =    lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & (njets_CBT123 >= 2) & (nfwd==0)

# ===== Rescales ===== #

ttb_1p25_rescale = lambda w: w*1.25