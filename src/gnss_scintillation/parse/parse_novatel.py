# parse_novatel.py

import gzip
from struct import unpack
import numpy as np

# Reference Document: https://chain-new.chain-project.net/docs/Novatel/Gsv4004BManualFeb_07.pdf

class ParseNovatel:

    def __init__(self, filename):

#    def read_file(filename):
        # Hard coded assumptions in this function:
        # 32 PRNs (0-31)
        # 50 Hz data
        # Only 1 frequency (L1)
    
        # initialize arrays to store data in
        self.tstmp_wnc = list()
        self.tstmp_tow = list()
        self.tstmp_tec_wnc = list()
        self.tstmp_tec_tow = list()
        self.phase = {prn:list() for prn in range(32)}
        self.power = {prn:list() for prn in range(32)}
        self.tec = {prn:list() for prn in range(32)}
        self.dtec = {prn:list() for prn in range(32)}
    
        with gzip.open(filename, 'rb') as f:
    
            while True:
    
                # Read Header
                try:
                    block_id, block_length, wnc, tow = self.read_header(f)
                    #print(block_id)
                except EOFError:
                    # At EOF, exit while loop
                    break
        
                # read block
                if block_id == 327:
                    adr, pwr, tec0, dtec0 = self.read327(f)
        
                    # organize output from block
                    self.tstmp_wnc.extend(np.full(50, wnc))
                    self.tstmp_tow.extend(tow+np.arange(0., 1000., 20.))
    
                    self.tstmp_tec_wnc.append(wnc)
                    self.tstmp_tec_tow.append(tow)
    
                    for prn in range(32):
                        self.phase[prn].extend(adr[prn-1,:])
                        self.power[prn].extend(pwr[prn-1,:])
                        self.tec[prn].append(tec0[prn-1])
                        self.dtec[prn].append(dtec0[prn-1])
        
                else:
                    # skip block
                    f.read(block_length)

   
        # Any final organization?
        # convert timestamps
        # convert to pandas dataframe?
        #print(tstmp_wnc, tstmp_tow)
        #print(phase.keys())
    
#        if return_tec:
#            return tstmp_wnc, tstmp_tow, phase, power, tstmp_tec_wnc, tstmp_tec_tow, tec, dtec
#        else:
#            return tstmp_wnc, tstmp_tow, phase, power


    def read_header(self, fp):
    
        header = fp.read(28)
        
        # If header empty, end of file has been reached.
        if not header:
            raise EOFError
    
        _, _, _, HeaderLength, MessageID, _, _, MessageLength, _, _, _, wnc, tow, _, _, _ = unpack('=BBBBHBBHHBBHLLHH', header)
    
        return MessageID, MessageLength+4, wnc, tow
    
    
    def read327(self, f):
        
        block_data = dict()
    
        # read number of PRNs
        data = f.read(4)
        N, = unpack('=i', data)
    
        adr = np.full((32, 50), np.nan)
        pwr = np.full((32, 50), np.nan)
        tec = np.full((32,), np.nan)
        dtec = np.full((32,), np.nan)
    
        # cycle through each prn
        for _ in range(N):
    
            data = f.read(20)
            prn, _, tec0, dtec0, adr0 = unpack('=hhffd', data)
    
            tec[prn-1] = tec0
            dtec[prn-1] = dtec0
    
            for i in range(50):
                data = f.read(8)
                dadr, powr = unpack('=iI', data)
                adr[prn-1,i] = adr0+dadr/1000.
                pwr[prn-1,i] = powr
    
        f.read(4)
        
        return adr, pwr, tec, dtec
    
    
    
#    def read_file(filename, return_tec=False):
#        # Hard coded assumptions in this function:
#        # 32 PRNs (0-31)
#        # 50 Hz data
#        # Only 1 frequency (L1)
#    
#        # initialize arrays to store data in
#        tstmp_wnc = list()
#        tstmp_tow = list()
#        tstmp_tec_wnc = list()
#        tstmp_tec_tow = list()
#        phase = {prn:{'L1':list()} for prn in range(32)}
#        power = {prn:{'L1':list()} for prn in range(32)}
#        tec = {prn:{'L1':list()} for prn in range(32)}
#        dtec = {prn:{'L1':list()} for prn in range(32)}
#    
#        with gzip.open(filename, 'rb') as f:
#    
#            while True:
#    
#                # Read Header
#                try:
#                    block_id, block_length, wnc, tow = read_header(f)
#                    #print(block_id)
#                except EOFError:
#                    # At EOF, exit while loop
#                    break
#        
#                # read block
#                if block_id == 327:
#                    adr, pwr, tec0, dtec0 = read327(f)
#        
#                    # organize output from block
#                    tstmp_wnc.extend(np.full(50, wnc))
#                    tstmp_tow.extend(tow/1000.+np.arange(0., 1., 0.02))
#    
#                    tstmp_tec_wnc.append(wnc)
#                    tstmp_tec_tow.append(tow/1000.)
#    
#                    for prn in range(32):
#                        phase[prn]['L1'].extend(adr[prn-1,:])
#                        power[prn]['L1'].extend(pwr[prn-1,:])
#                        tec[prn]['L1'].append(tec0[prn-1])
#                        dtec[prn]['L1'].append(dtec0[prn-1])
#        
#                else:
#                    # skip block
#                    f.read(block_length)
#    
#        # Any final organization?
#        # convert timestamps
#        # convert to pandas dataframe?
#        #print(tstmp_wnc, tstmp_tow)
#        #print(phase.keys())
#    
#        if return_tec:
#            return tstmp_wnc, tstmp_tow, phase, power, tstmp_tec_wnc, tstmp_tec_tow, tec, dtec
#        else:
#            return tstmp_wnc, tstmp_tow, phase, power


#def summary_plot(filename):
#    import matplotlib.pyplot as plt
#
#    wnc, tow, phase, power = read_file(filename)
#
#    fig = plt.figure(figsize=(10,10))
#    ax1 = fig.add_subplot(211)
#    ax1.set_title('Phase')
#    ax2 = fig.add_subplot(212)
#    ax2.set_title('Power')
#    for prn in range(32):
#        ax1.plot(tow, phase[prn]['L1'])
#        ax2.plot(tow, power[prn]['L1'])
#    plt.show()


