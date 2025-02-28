# utils.py
# Shared utility functions

# import spacepy.time as spt
import numpy as np


def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is


#def gps2utc(wnc, tow):
#    # Convert GPS timestamps to numpy.datetim64 array
#
#    # tstmp = np.datetime64('1980-01-06') + wnc.astype('timedelta64[W]') + (tow*1000.).astype('timedelta64[ms]')
#    # tm = spt.Ticktock(tstmp.astype('datetime64[s]').astype(int), 'UNX')
#    # utc_tstmp = tstmp-(tm.leaps.astype('timedelta64[s]')-19)
#
#    tm = spt.Ticktock(wnc*7*24*60*60+tow, 'GPS')
#    utc_tstmp = np.array(tm.UTC, dtype='datetime64')
#    
#    return utc_tstmp

