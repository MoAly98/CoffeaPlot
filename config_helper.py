from omegaconf import OmegaConf
from classes import Functor

# ==== Variables ==== #

variables = {
    'bdt_tH': lambda x: x[:,0],
    'bdt_ttb': lambda x: x[:,1],
}
# OmegaConf.register_new_resolver("bdt_tH", lambda x: x[:,0])
# OmegaConf.register_new_resolver("bdt_ttb", lambda x: x[:,1])


# ===== Weights ===== #

def MC_weight(xsec_weight, weight_mc,weight_pileup, weight_bTagSF_DL1r_Continuous,weight_jvt,weight_forwardjvt,weight_leptonSF, runNumber,totalEventsWeighted):
    return (36646.74*(runNumber<290000)+44630.6*((runNumber>=290000) & (runNumber<310000))+58791.6*(runNumber>=310000))*weight_mc*xsec_weight*weight_pileup*weight_bTagSF_DL1r_Continuous*weight_jvt*weight_forwardjvt*weight_leptonSF/totalEventsWeighted

def MM_weight(mm_weight):
    return mm_weight[:, 0]

weights = {
    'mc_weight': MC_weight,
    'mm_weight': MM_weight,
}
# OmegaConf.register_new_resolver("mc_weight", MC_weight)
# OmegaConf.register_new_resolver("mm_weight", MM_weight)

# ===== Selection ===== #
# Selection
tight_lepton = lambda lepton_tight: lepton_tight[:,0] == 1
xxx_is_c     = lambda HFClass: HFClass == -1
xxx_is_b     = lambda HFClass: HFClass == 1
xxx_is_light = lambda HFClass: HFClass == 0

ttb_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_b(y))
ttc_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_c(y))
ttl_cut = lambda x, y: (tight_lepton(x)) & (xxx_is_light(y))

selections = {
    'ttb_cut': ttb_cut,
    'ttc_cut': ttc_cut,
    'ttl_cut': ttl_cut,
    'leptight_cut': tight_lepton,
}
# OmegaConf.register_new_resolver("ttb_cut", ttb_cut)
# OmegaConf.register_new_resolver("ttc_cut", ttc_cut)
# OmegaConf.register_new_resolver("ttl_cut", ttl_cut)
# OmegaConf.register_new_resolver("leptight_cut", tight_lepton)


# ===== Regions ===== #
# PRESEL
PR_fn     =    lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0)
# SIGNAL REGIONS
SR_fn     =    lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & (njets_CBT123 < 2) & (nfwd>0)
# TTB CR REGIONS
CR_ttb_fn =    lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & (njets_CBT123 >= 2) & (nfwd==0)

regions = {
    'PR': PR_fn,
    'SR': SR_fn,
    'CR': CR_ttb_fn,
}
# OmegaConf.register_new_resolver("PR_fn", PR_fn)
# OmegaConf.register_new_resolver("SR_fn", SR_fn)
# OmegaConf.register_new_resolver("CR_ttb_fn", CR_ttb_fn)

# ===== Rescales ===== #

rescales = {
    'ttb_1p25_rescale': lambda w: w*1.25,
}


helpers = {**variables, **weights, **selections, **regions, **rescales}