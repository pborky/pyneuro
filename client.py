
import re

import socket

import threading
from threading import Thread,Lock,Event,RLock
from Queue import Queue,Full,Empty

from time import sleep

from pyneuro import NeuroError,NeuroTimeout,Neuro

class NeuroClient(Neuro):
    def __init__(self, address, device, role):
        Neuro.__init__(self, address, device)
        self.role = role
    
    def checkResponse(self, msg):
        if len(msg) < 6 or cmp(msg[0:6],"200 OK") != 0:
            raise NeuroError("Wrong response.")

    def open(self):
        try:
            self.socket = socket.create_connection(self.address)
            self.send(self.role)
            msg = self.recv()
            self.checkResponse(msg)
        except socket.error:
            raise NeuroError("Error opening socket.")

class NeuroClientEEG(NeuroClient):
    def __init__(self, address, device):
        NeuroClient.__init__(self, address, device, "eeg")
        self.device = device
        self.lastSeq = -1
        self.samples = -1

    def sendHeader(self):
        try:
            self.send("setheader "+self.device.getHeader()+"\r\n")
            msg = self.recv()
            self.checkResponse(msg)
        except socket.error:
            raise NeuroError("Error opening socket.")

    def sendData(self):
        for packet in self.device.getData():
            if self.lastSeq > -1 and self.lastSeq + 1 != packet[0]:
                raise NeuroError("Sequence number not consistent.")
            self.lastSeq = packet[0]
            if self.samples > 0:
                if self.samples != packet[1] and self.samples + 2 != len(packet):
                    raise NeuroError("Packet size not consistent.")
            else:
                self.samples = packet[1]
            # FIXME: bastl:
            s = "".join([ " {"+str(i+2)+"}" for i in range(self.samples) ])
            self.send(("! {0} {1}"+ s).format(*packet))
            msg = self.recv()
            self.checkResponse(msg)
    
    def run(self):
        NeuroClient.run(self)
        self.sendHeader()
        while True:
            self.sendData()

class NeuroSocketProducer(Thread):
    def __init__(self, caller):
        threading.Thread.__init__(self)
        self.caller = caller
        self.queues = {}
        self.clients = {}
        self.lastSeq = None
        self.name = "ReceiverThread"
        self.daemon = True

    def getQueues(self, clId = None):
        if clId is None:
            return self.caller.getQueues()
        if clId not in self.queues: # thread local copy of queues
            self.queues = self.caller.getQueues()
        return self.queues[clId]
    
    def parseSamples(self, lines):
        for line in lines: # self.recvLines():
            if cmp(line[0:6],"200 OK") == 0:
                continue
            line = line.split()
            if len(line) < 1 or line[0] != '!':
                #raise NeuroError("Wrong packet received.")
                print "Wrong packet received."
            try:
                clId, seq , nSampl = [ int(i) for i in line[1:4] ]
            except ValueError:
                #raise NeuroError("Wrong packet received.")
                print "Wrong packet received."

            sampl = [ float(i) for i in line[4:] ]
           
            if self.lastSeq is not None:
                if seq != self.lastSeq + 1:
                    self.lastSeq = seq
                    #raise NeuroError("Packet sequence error (seq = {0}).".format(seq))
                    print "Oops! Packet sequence error (seq = {0}).".format(seq)
                else:
                    self.lastSeq = self.lastSeq + 1
            else:
                self.lastSeq = seq

            if clId not in self.clients:
                self.clients[clId] = tuple([[]]*nSampl) # tuple of empty lists
            if nSampl != len(self.clients[clId]):
                #raise NeuroError("Wrong packet length.")
                print "Wrong packet length."
            for i in range(nSampl):
                self.clients[clId][i].append(sampl[i])
    
    def recvLines(self):
        msg = self.caller.recv()
        if msg == '':
            raise NeuroError("No more data. Is socket open?")
        while len(msg) < 1 or msg[-1] != '\n':
            msg += self.caller.recv()
        return msg.splitlines()
    
    def enqueueSamples(self):
        queues = self.getQueues()
        for i in self.clients.copy():
            try:
                queues[i].put(self.clients[i], True, 1.0)
            except Full:
                print "Queue busy. Dropping packets."
            del self.clients[i]

    def run(self):
        self.lastSeq = -1
        while not self.caller.terminate.isSet():
            self.caller.watching.wait(1.0)
            if not self.caller.watching.isSet():
                continue
            try:
                lines = self.recvLines()
            except NeuroError as e:
                print "Oops!! {0} got: {1}".format(threading.currentThread().name, e)
                break
            self.parseSamples(lines)
            self.enqueueSamples()
                

class NeuroClientDisp(NeuroClient):
    def __init__(self, address, queueSize = 0):
        NeuroClient.__init__(self, address, None, "display")
        self.queueSize = queueSize
        self.clients = {}
        self.queues = {}
        self.queuesLock = Lock()
        self.watching = Event()
        self.terminate = Event()
        self.watching.clear()
        self.terminate.clear()
        self.provider = NeuroSocketProducer(self)
        self.provider.start()

    def setRole(self, cl, value):
        self.clients[cl][0] = value

    def setHeader(self, cl, value):
        self.clients[cl][1] = value

    def setWatching(self, cl, value):
        self.clients[cl][2] = value

    def getRole(self, cl):
        return self.clients[cl][0]

    def getHeader(self, cl):
        return self.clients[cl][1]

    def isWatching(self, cl):
        return self.clients[cl][2]

    def isWatchingAny(self):
        for cl in self.clients.values():
            if cl[2]:
                return True
        return False
    
    def checkProvider(self):
        if not self.provider.isAlive():
            raise NeuroError("Data receiving worker found dead. Possibily connection error.")
    
    def getQueues(self, client = None):
        self.queuesLock.acquire()
        try:
            if client is None:
                q = self.queues.copy()
            else:
                q = self.queues[client]
        finally:
            self.queuesLock.release()
        return q

    def getData(self, client, minLength = 0):
        self.checkProvider()

        data = ()
        queue = self.getQueues(client)
        
        while len(data) == 0 or len(data[0]) < minLength:
            try:
                samples = queue.get(True, 1.0)
            except Empty:
                break

            if len(data) == 0:
                data = samples
            else:
                nSampl = None
                for i in range(len(samples)):
                    if nSampl == None:
                        nSampl = len(samples[i])
                    else:
                        if nSampl == len(samples[i]):
                            raise NeuroError("Packet length is not consistent.")
                    data[i].extend(samples[i])
        
        return data

    def recvStatus(self):
        if self.watching.isSet():
            return
        self.send("status")
        lines = self.recv().splitlines()
        while len(lines) < 2:
            sleep(.1)
            lines.extend(self.recv().splitlines())
        self.checkResponse(lines.pop(0))
        m = re.match(r'([0-9]+)\s+clients connected', lines.pop(0))
        if m is None:
            raise NeuroError("Unexpected response.")
        n = int(m.group(1))
        while len(lines) < n:
            sleep(.1)
            lines.extend(self.recv().splitlines())
        self.clients = {}
        self.queuesLock.acquire()
        try:
            self.queues = {}
            for i in range(n):
                m = re.match(r'([0-9]+):(.*)', lines.pop(0))
                if m is None:
                    raise NeuroError("Unexpected response.")
                key, clientType = m.groups()
                key = int(key)
                self.clients[key] = [clientType,None,False]
                if self.getRole(key) == 'EEG':
                    self.recvHeader(key)
                    self.queues[key] = Queue(self.queueSize)
        finally:
            self.queuesLock.release()

    def recvHeader(self, client):
        if self.watching.isSet():
            return
        if client not in self.clients:
            self.recvStatus()
            if client not in self.clients:
                raise NeuroError("Client #{0} not present.".format(client))
        if self.getRole(client) != 'EEG':
            raise NeuroError("Client #{0} is not EEG device.".format(client))
        self.send('getheader {0}'.format(client))
        lines = self.recv().splitlines()
        while len(lines) < 2:
            sleep(.1)
            lines.extend(self.recv().splitlines())
        self.checkResponse(lines.pop(0))
        self.setHeader(client, lines.pop(0))

    def unwatch(self, client):
        self.checkProvider()
        if client not in self.clients:
            raise NeuroError("Client #{0} not present.".format(client))
        if self.getRole(client) != 'EEG':
            raise NeuroError("Client #{0} is not EEG device.".format(client))
        if not self.isWatching(client):
            return
        self.send('unwatch {0}'.format(client))
        self.setWatching(client, False)
        if not self.isWatchingAny():
            self.watching.clear()

    def watch(self, client):
        self.checkProvider()
        if client not in self.clients:
            raise NeuroError("Client #{0} not present.".format(client))
        if self.getRole(client) != 'EEG':
            raise NeuroError("Client #{0} is not EEG device.".format(client))
        if self.isWatching(client):
            return
        self.send('watch {0}'.format(client))
        self.setWatching(client, True)
        self.watching.set()

    def run(self):
        NeuroClient.run(self)
        self.recvStatus()



