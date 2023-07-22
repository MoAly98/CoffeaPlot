from classes import *

rescales = [
    Rescale('ttb_1p25',['ttb'], Functor(lambda w: w*1.25, ['weights'])),
]

rescales_list = Rescales(rescales)