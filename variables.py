from classes import *

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
