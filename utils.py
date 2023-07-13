from collections import defaultdict
import numpy as np

def dd4():
    return defaultdict(int)
def dd3():
    return defaultdict(dd4)
def dd2():
    return defaultdict(dd3)
def dd1():
    return defaultdict(dd2)
def dd():
    return defaultdict(dd1)

def deep_map():
    return defaultdict(deep_map)


def remove_unwanted_samples(sample_to_hists_dict, unwanted):
    return {k: v for k, v in sample_to_hists_dict.items() if k not in unwanted}

def get_blinding(s_h, b_h, threshold = 0.00333):
    signal_vals = s_h.values()
    bkg_vals    = b_h.values()
    sqrt_bkg    = np.sqrt(bkg_vals, out = np.full_like(bkg_vals, 0), where = bkg_vals>=0)
    s_over_b    = np.divide(signal_vals,  bkg_vals, out = np.full_like(bkg_vals, 0),  where = bkg_vals>0)
    print(s_over_b)
    return s_over_b > threshold

def compute_total_separation(signal_h, bkg_h):

    numBins      = len(signal_h.axes.centers[0])
    intBins      = (signal_h.axes.edges[0][-1] - signal_h.axes.edges[0][0])/numBins
    total_signal = sum(signal_h.values(flow=True))
    total_bkg    = sum(bkg_h.values(flow=True))

    nS = total_signal*intBins
    nB = total_bkg*intBins

    if nS>0 and nB >0:

        s = signal_h.values()/nS
        b = bkg_h.values()/nB

        separation   = sum(0.5*np.divide((s-b)**2, (s+b), out = np.full_like(s, 0), where = (s+b)>0))
        separation  *= intBins

    else:
        separation = 0

    return separation

def compute_total_significance(signal_h, bkg_h):
    signal_vals  = signal_h.values(flow=True)
    bkg_sqrt_vals = np.sqrt(bkg_h.values(flow=True), out=np.full_like(bkg_h.values(flow=True), 0), where=bkg_h.values(flow=True)>0)
    signficance = sum(signal_vals)/sum(bkg_sqrt_vals) if sum(bkg_sqrt_vals) > 0 else 0

    return signficance

def get_signif_per_bin(signal_h, bkg_h):

    signal_vals  = signal_h.values()
    signal_var   = signal_h.variances()
    bkg_vals     = bkg_h.values()
    bkg_var      = bkg_h.variances()


    sqrt_bkg_vals = np.sqrt(bkg_vals,                      out=np.full_like(signal_h.axes.centers[0], 0), where=bkg_vals>0)
    signficance   = np.divide(signal_vals, sqrt_bkg_vals,  out=np.full_like(signal_h.axes.centers[0], 0), where=sqrt_bkg_vals>0.001)

    err1          = (1/4)*np.divide(bkg_var, bkg_vals**2,   out=np.full_like(signal_h.axes.centers[0], 1e3), where=bkg_vals>0.001)
    err2          = np.divide(signal_var, signal_vals**2,   out=np.full_like(signal_h.axes.centers[0], 1e3), where=signal_vals>0.001)

    signficance_err  = signficance*np.sqrt(err1+err2,      out=np.full_like(signal_h.axes.centers[0], 1e3), where=err1+err2>=0)

    return signficance, signficance_err