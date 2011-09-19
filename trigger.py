
from pyneuro import NeuroDevice
from Queue import Queue,Full,Empty
from threading import Thread,Timer,RLock
from time import sleep

TRIGGER_HEADER = '''0       TRIGGERING USER                                                                 PBORKY                                                                          03.03.1017.51.36512     BIOSEMI                                     -1      1       1   PBORKY RAW      UNIVERSAL                                                                       mV           0    255        0    255   No prefiltering, raw data from NIA                                              4000                                    '''
        
class TriggerDeviceThread(Thread):
    def __init__(self, caller):
        Thread.__init__(self)
        self.caller = caller
        self.freq = caller.freq
        self.seq = 0
        self.channels = caller.channels
        self.name = "TriggerDeviceThread"
        self.daemon = True
    
    def run(self):
        while True:
            if self.caller.queue.full():
                print "TriggerDevice: Queue busy."
            else:
                val = self.caller.getValues()
                self.caller.queue.put([ (self.seq+i, self.channels) + val for i in range(10) ])
            self.seq += 10
            sleep(10.0/self.freq)

class TriggerDevice(NeuroDevice):
    def __init__(self, freq, header = TRIGGER_HEADER):
        self.freq = freq
        self.channels = 1
        self.header = header
        self.values = [0,]*self.channels
        self.valLock = RLock()
        self.queue = Queue(100000)
        self.thread = TriggerDeviceThread(self)
        self.thread.start()
    
    def getValues(self):
        self.valLock.acquire()
        try:
            return tuple(self.values)
        finally:
            self.valLock.release()
    
    def setValues(self, val):
        self.valLock.acquire()
        try:
            self.values[:] = val
        finally:
            self.valLock.release()

    def getHeader(self):
        return self.header
    
    def getData(self):
        return self.queue.get(10.0)
        