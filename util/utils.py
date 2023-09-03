import numpy as np

def keys_to_lower(mydict):
    newdict = {}
    for k in mydict.keys():
        if isinstance(mydict[k], dict):
            newdict[k.lower()] = keys_to_lower(mydict[k])
        else:
            if isinstance(mydict[k], list):
                newdict[k.lower()] = [keys_to_lower(i) if isinstance(i, dict) else i for i in mydict[k]]
            else:
                newdict[k.lower()] = mydict[k]

    return newdict

def compute_total_separation(signal_h, bkg_h):

    n_bins       = len(signal_h.values())
    bin_widths   = (signal_h.axes.edges[0][-1] - signal_h.axes.edges[0][0])/n_bins
    total_signal = sum(signal_h.values(flow=True))
    total_bkg    = sum(bkg_h.values(flow=True))

    nS = total_signal*bin_widths
    nB = total_bkg*bin_widths

    if nS>0 and nB >0:

        s = signal_h.values()/nS
        b = bkg_h.values()/nB

        separation   = sum(0.5*np.divide((s-b)**2, (s+b), out = np.full_like(s, 0), where = (s+b)>0))
        separation  *= bin_widths

    else:
        separation = 0

    return separation