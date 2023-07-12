from classes import *

# PRESEL
PR_fn =    lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0)
# SIGNAL REGIONS
SR_fn    =  lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & (njets_CBT123 < 2) & (nfwd>0)
# TTB CR REGIONS
CR_ttb_fn        = lambda njets, nbjets, njets_CBT4, njets_CBT5, njets_CBT123, tau_pt, nfwd:  (~((njets>=5) & (nbjets>=4))) & (ak.num(tau_pt, axis=1) == 0) & ((njets_CBT4+njets_CBT5) >= 3) & (njets_CBT123 >= 2) & (nfwd==0)

regions_list = [

    Region('PR', Functor(PR_fn, ['njets','nbjets','njets_CBT4', 'njets_CBT5', 'njets_CBT123', 'tau_pt','nfwdjets'])),
    Region('SR', Functor(SR_fn, ['njets','nbjets','njets_CBT4', 'njets_CBT5', 'njets_CBT123', 'tau_pt','nfwdjets']), ['tH']),
    Region('CR', Functor(CR_ttb_fn, ['njets','nbjets','njets_CBT4', 'njets_CBT5', 'njets_CBT123', 'tau_pt','nfwdjets']), ['ttb','tH']),

]

plot_regions = Regions(regions_list)