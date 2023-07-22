from classes import *
import numpy as np

plots_to_make = []

plot_list_1D = [
    # Variable('new_bdt_tH', Functor(lambda x: x[:,0], ['BDT']), [0, 0.3528, 0.6, 0.78, 1],   'NewBDT(tH)'),

    #Variable('alt_bdt_tH',Functor(lambda x: x[:,0], ['BDT_alt']), [0, 0.346, 0.593, 0.786, 1], 'AltBDT(tH)'),
    Variable('alt_bdt_tH',Functor(lambda x: x[:,0], ['BDT_alt']), np.linspace(0,1, 20), 'AltBDT(tH)'),


    # Variable('sim_bdt_tH',Functor(lambda x: x[:,0], ['BDT_sim']),  [0, 0.424, 0.64, 0.795, 1], 'SimpleBDT(tH)'),

    # Variable('new_bdt_ttb',Functor(lambda x: x[:,1], ['BDT']), [0,0.2,0.3,0.4,0.5,1.0],     'NewBDT(ttb)'),

    Variable('alt_bdt_ttb',Functor(lambda x: x[:,1], ['BDT_alt']), [0,0.2,0.3,0.4,0.5,1.0], 'AltBDT(ttb)'),

    # Variable('sim_bdt_ttb',Functor(lambda x: x[:,1], ['BDT_sim']), [0,0.2,0.3,0.4,0.5,1.0],     'SimpleBDT(ttb)'),

]

plots_1d_nom = Variables(1, 'nominal_Loose', plot_list_1D)
plots_to_make.append(plots_1d_nom)

plots_2d_nom = Variables(2, 'nominal_Loose')
plots_to_make.append(plots_2d_nom)
