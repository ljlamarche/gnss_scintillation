# parse_septentrio.py

import gzip
from struct import unpack
import numpy as np
from .utils import twos_comp, gps2utc

# Reference Document: https://chain-new.chain-project.net/docs/Septentrio/PolaRxSPro/PolaRxS-Firmware-v2.9.0-SBF-Reference-Guide.pdf

def read_header(fp):
    
    header = fp.read(8)
    
    # If header empty, end of file has been reached.
    if not header:
        raise EOFError

    sync1, sync2, crc, id0, length = unpack('=ccHHH', header)
    # Only use first 12 bits for block ID
    id0 = id0 & 0xfff   # Block ID
 
    return id0, length

signal_type = {0 : {'name':'GPS_L1-CA', 'freq':1575.42*1.e6},
               1 : {'name':'GPS_L1-P(Y)', 'freq':1575.42*1.e6},
               2 : {'name':'GPS_L2-P(Y)', 'freq':1227.60*1.e6},
               3 : {'name':'GPS_L2C', 'freq':1227.60*1.e6},
               4 : {'name':'GPS_L5', 'freq':1176.45*1.e6}}


def read4027(f):
    
    # read time of week (ms), week #, # of satellites, length of sat info block
    data = f.read(9)
    tow, wnc, N1, SB1length, SB2length  = unpack('=IHBBB', data)
    
    # read common flags, cumulative clock jumps (ms)
    # Note: clock jumps may be important later???
    data = f.read(3)
    CommonFlags, CumClkJumps, _ = unpack('=BBB', data)

    CarrierPhase = np.full((32,len(signal_type)), np.nan)

    for n in range(N1):
    #   data = f.read(SB1length)

        # START READING MeasEpochChannelType1 Subblock HERE
        data = f.read(3)
        RxChannel, typ, svid = unpack('=BBB', data)
        typ = typ & 0x1F

        # pseudorange (MIGHT be correct???)
        data = f.read(5)
        misc, codeLSB = unpack('=BI', data)
        codeMSB = misc & 0xF
        pseudorange = (codeMSB*4294967296+codeLSB)*0.001

        # doppler
        data = f.read(4)
        dopp, = unpack('=i', data)
        doppler = dopp*0.0001

        # carrier phase
        data = f.read(3)
        carrierLSB, carrierMSB = unpack('=Hb', data)

        lam = 299792458/signal_type[typ]['freq']

        carrier_phase = pseudorange/lam + (carrierMSB*65536+carrierLSB)*0.001
        CarrierPhase[svid-1,typ] = carrier_phase

        # CN0
        data = f.read(1)
        CN0, = unpack('=B', data)
        if typ in [1,2]:
            CN0 = CN0*0.25
        else:
            CN0 = CN0*0.25+10 # This equation changes depending on typ

        # Lock time
        data = f.read(2)
        locktime, = unpack('=H', data)

        # observation info, N2
        data = f.read(2)
        obs_info, N2 = unpack('=BB', data)

        # START READING MeasEpochChannelType2 Subblock HERE
        for i in range(N2):
            data = f.read(SB2length)
            typ2, locktime, CN0, offsetMSB, carrierMSB2, obs_info, codeoffsetLSB, carrierLSB2, doppleroffsetLSB, = unpack('=BBBBbBHHH', data)
            typ2 = typ2 & 0x1F
            if typ in [1,2]:
                CN0 = CN0*0.25
            else:
                CN0 = CN0*0.25+10 # This equation changes depending on typ

            CodeOffsetMSB = twos_comp((offsetMSB & 0x7), 3) 
            DopplerOffsetMSB = twos_comp((offsetMSB & 0xF8) >> 3, 5)

            pseudorange2 = pseudorange + (CodeOffsetMSB*65536+codeoffsetLSB)*0.001
            lam2 = 299792458/signal_type[typ2]['freq']
            carrier_phase2 = pseudorange2/lam2 +(carrierMSB2*65536+carrierLSB2)*0.001
            alpha = signal_type[typ2]['freq']/signal_type[typ]['freq']
            doppler2 = doppler*alpha + (DopplerOffsetMSB*65536+doppleroffsetLSB)*1e-4

            CarrierPhase[svid-1,typ2] = carrier_phase2

    return tow, wnc, CarrierPhase


def read4046(fp):

    # read time of week (ms), week #, # of satellites, length of sat info block
    data = fp.read(8)
    tow, wnc, N, SBlength  = unpack('=IHBB', data)

    # read common flags, cumulative clock jumps (ms)
    # Note: clock jumps may be important later???
    data = fp.read(4)
    CorrDuration, CumClkJumps, _, _ = unpack('=BBBB', data)

    # create empty arrays to fill
    Icorr = np.full((32,len(signal_type)), np.nan)
    Qcorr = np.full((32,len(signal_type)), np.nan)
    CarrierPhase = np.full((32,len(signal_type)), np.nan)

    # read each message subblock
    for n in range(N):

      # read RxChannel, type, SVID
      data = fp.read(3)
      RxChannel, typ, svid = unpack('=BBB', data)
      typ = typ & 0x1F
    
      # read CorrIQ LSB and MSB, Carrier phase LSB
      data = fp.read(5)
      CorrIQ_MSB, CorrI_LSB, CorrQ_LSB, CarrierPhaseLSB = unpack('=BBBH', data)
      CorrI_MSB = twos_comp((CorrIQ_MSB & 0xF), 4)
      CorrQ_MSB = twos_comp((CorrIQ_MSB & 0xF0) >> 4, 4)

      Icorr[svid-1,typ] = CorrI_MSB*256 + CorrI_LSB
      Qcorr[svid-1,typ] = CorrQ_MSB*256 + CorrQ_LSB
      CarrierPhase[svid-1,typ] = CarrierPhaseLSB*0.001

    return tow, wnc, Icorr, Qcorr, CarrierPhase


def read_file(filename):

    # initialize arrays to store data in
    tstmp_wnc = list()
    tstmp_tow = list()
    phase = {prn:{sig_info['name']:list() for sig_info in signal_type.values()} for prn in range(32)}
    power = {prn:{sig_info['name']:list() for sig_info in signal_type.values()} for prn in range(32)}

    tstmp_wnc_ME = list()
    tstmp_tow_ME = list()
    carrier_phase_ME = list()

    with gzip.open(filename, 'rb') as f:

        # Read through all blocks to end of file
        while True:

            # Read Header
            try:
                block_id, block_length = read_header(f)
            except EOFError:
                # At EOF, exit while loop
                break


            # read block
            if block_id == 4046:
                tow, wnc, I, Q, cp = read4046(f)
    
                # organize output from block
                tstmp_wnc.append(wnc)
                tstmp_tow.append(tow/1000.)

                for prn in range(32):
                    for st, sig_info in signal_type.items():
                        power[prn][sig_info['name']].append(I[prn,st]**2 + Q[prn,st]**2)
                        phase[prn][sig_info['name']].append(cp[prn,st])


            elif block_id == 4027:
                tow, wnc, cp = read4027(f)
                tstmp_wnc_ME.append(wnc)
                tstmp_tow_ME.append(tow/1000.)
                carrier_phase_ME.append(cp)
    
            else:
                # skip block
                f.read(block_length-8)

    # Any final organization?
    # convert timestamps
    # convert to pandas dataframe?

    #carrier_phase_IQ = np.array(carrier_phase.copy())

    #Icorr = np.array(Icorr)
    #Qcorr = np.array(Qcorr)
    #carrier_phase = np.array(carrier_phase)
    carrier_phase_ME = np.array(carrier_phase_ME)

    #for i in range(len(tstmp_tow_ME)):
    #    carrier_phase[i*100:(i+1)*100,:,:] = np.unwrap(carrier_phase[i*100:(i+1)*100,:,:], axis=0, period=65.536) + carrier_phase_ME[i,:,:]

    #carrier_phase = [carrier_phase[i*100:(i+1)*100]+carrier_phase_ME[i] for i in range(len(tstmp_tow_ME))]

    #print(len(tstmp_tow), len(tstmp_tow_ME))
    #print(carrier_phase_IQ[:100,16,0])
    #print(np.diff(carrier_phase_ME[:10,16,0]))


    for prn in range(32):
        for st, sig_info in signal_type.items():
            #phase[prn][sig_info['name']] = np.unwrap(phase[prn][sig_info['name']], period=65.536)
            for i in range(len(carrier_phase_ME)):
                phase[prn][sig_info['name']][i*100:(i+1)*100] = np.unwrap(phase[prn][sig_info['name']][i*100:(i+1)*100], period=65.536) + carrier_phase_ME[i,prn,st]


    #tstmp = gps2utc(tstmp_wnc, tstmp_tow)

    return tstmp_wnc, tstmp_tow, phase, power


def summary_plot(filename):
    import matplotlib.pyplot as plt

    wnc, tow, phase, power = read_file(filename)

    fig = plt.figure(figsize=(10,10))
    ax1 = fig.add_subplot(211)
    ax1.set_title('Phase')
    ax2 = fig.add_subplot(212)
    ax2.set_title('Power')
    for prn in range(32):
        ax1.plot(tow, phase[prn]['GPS_L1-CA'])
        ax2.plot(tow, power[prn]['GPS_L1-CA'])
    plt.show()


