from classes import *

rescales_list = [
    Rescale('ttb_1p25',['ttb'], Functor(lambda w: w*1.25, ['weights'])),
]

plot_rescales = Rescales(rescales_list)