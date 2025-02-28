# detrend.py
# Functions to detrend the power and phase timeseries

import numpy as np
from scipy import signal

def power_detrend(power, datarate=50, cutoff=0.1):

    sos = signal.butter(6, cutoff, 'low', fs=datarate, output='sos')
    trend = signal.sosfiltfilt(sos, power)

    power_detrend = power/trend
    
    return power_detrend


def phase_detrend(phase, datarate=50, cutoff=0.1):

    sos = signal.butter(6, cutoff, 'high', fs=datarate, output='sos')
    phase_detrend = signal.sosfiltfilt(sos, phase)

    return phase_detrend

# def phase_detrend_bp(utime, phase, cutoff_low=0.0005, cutoff_high=0.1):
#     datarate = 1./np.mean(np.diff(utime))
#     sos = signal.butter(6, [cutoff_low, cutoff_high], 'bandpass', fs=datarate, output='sos')
#     phase_detrend = signal.sosfiltfilt(sos, phase)

#     return phase_detrend