# scint_index.py
# Basic functions to caluclate scintillation indices, S_4 (power) and sigma_phi (phase)

import numpy as np

def S_4(power, window, datarate=1):

    hw = int(window/2.*datarate)    # half window in points

    rw = np.lib.stride_tricks.sliding_window_view(power,hw*2)
    rw = np.delete(rw,len(rw)-1,0) # Delete last row for accurate results
    
    return np.concatenate(([np.nan]*hw,np.std(rw,axis=1,ddof=0) / abs(np.mean(rw,axis=1)), [np.nan]*hw), axis=None)


def sigma_phi(phase, window, datarate=1):

    hw = int(window/2.*datarate)    # half window in points

    rw = np.lib.stride_tricks.sliding_window_view(phase,hw*2)
    rw = np.delete(rw,len(rw)-1,0) # Delete last row for accurate results
    
    return np.concatenate(([np.nan]*hw, np.std(rw, axis=1, ddof=0), [np.nan]*hw), axis=None)
