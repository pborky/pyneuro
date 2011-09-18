#!/bin/env python

from pyneuro import NeuroDeviceUSB,NeuroDeviceError

NIA_VENDOR = 0x1234
NIA_PRODUCT = 0x0000
NIA_HEADER = '''0       OCZ NIA USER                                                                    OCZ NEURAL IMPULSE ACTUATOR                                                     03.03.1017.51.36512     BIOSEMI                                     -1      1       1   NIA RAW         UNIVERSAL                                                                       mV      -32768  32767   -32768  32767   No prefiltering, raw data from NIA                                              4000                                    '''

class NIAError(NeuroDeviceError):
    pass

class NIADevice(NeuroDeviceUSB):
    r"""Class for reading data of NIA device in higher level mode
    pyneuro"""
    def __init__(self, idVendor = NIA_VENDOR, idProduct = NIA_PRODUCT, header = NIA_HEADER):
        NeuroDeviceUSB.__init__(self, idVendor = idVendor, idProduct = idProduct, header = header)
        self.sequence = 0

    def getHeader(self):
        return self.header
    
    def getData(self):
        arr = self.endpoint.read(self.endpoint.wMaxPacketSize)
        retArray = []
        if len(arr) != 55:
            raise NIAError("Received data is inconsistent. Unexpected length: {0}".format(len(arr)))
        nsamp = arr[54]
        if nsamp > 16:
            raise NIAError("Received data is inconsistent. Unexpected number of samples: {0}".format(nsamp))
        for i in range(0,nsamp):
            b = arr[i*3 + 2]<<16 | arr[i*3 + 1]<<8 | arr[i*3]
            retArray.append((self.sequence, 1, (float(b)/256.0) - 32768))
            self.sequence = self.sequence + 1
        return retArray

