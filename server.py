
import re

import socket

import threading
from threading import Thread,Lock,Event,RLock
from Queue import Queue,Full,Empty

from time import sleep

from pyneuro import NeuroError,NeuroTimeout,Neuro,NeuroDevice

class NeuroDeviceProducer(Thread):
    def __init__(self, clId, caller):
        threading.Thread.__init__(self)
        self.clId = clId
        self.caller = caller
        self.queue = caller.getQueues(clId)
        self.lastSeq = None
        self.name = "DeviceThread-{0}".format(clId)
        self.daemon = True
    
    def run(self):
        while not self.caller.terminate.isSet():
            if len(self.caller.getWatchers(self.clId)) > 0:
                try:
                    self.queue.put(self.caller.recvData(self.clId),1.0)
                except Full:
                    raise NeuroError("Queue busy. Dropping packet(s).")
            
class NeuroSocketCommander(Thread):
    def __init__(self, clId, caller):
        threading.Thread.__init__(self)
        self.clId = clId
        self.caller = caller
        self.name = "CommanderThread-{0}".format(clId)
        self.daemon = True
    
    def run(self):
        while not self.caller.terminate.isSet():
            try:
                self.caller.recvCommands(self.clId)
            except NeuroTimeout as e:
                #print "*** Oops! Got: {0}".format(e)
                pass
            except NeuroError as e:
                print "*** Oops! {0} got: {1}".format(threading.currentThread().name, e)
                break
            self.caller.getClientsForRole('Display')
            if self.caller.isWatchingAny():
                self.caller.watching.set()
            else:
                self.caller.watching.clear()

class NeuroSocketConsumer(Thread):
    def __init__(self, clId, caller):
        threading.Thread.__init__(self)
        #self.clId = clId
        self.caller = caller
        #self.queue = caller.getQueues(clId)
        self.name = "SenderThread-{0}".format(clId)
        self.daemon = True
    
    def run(self):
        while not self.caller.terminate.isSet():
            eegs = self.caller.getClientsForRole('EEG')
            for eeg in eegs:
                watchers = self.caller.getWatchers(eeg)
                queue = self.caller.getQueues(eeg)
                if queue.empty():
                    continue
                try:
                    packet = queue.get(1.0)
                except Empty:
                    continue
                if len(watchers) == 0:
                    continue
                for watcher in watchers:
                    sock = self.caller.getSocket(watcher)
                    if sock is None:
                        print "No socket"
                        continue
                    try:
                        self.caller.send(packet, sock)
                    except NeuroError as e:
                        print "*** Oops! {0} got: {1}".format(threading.currentThread().name, e)

class NeuroServer(Neuro):
    def __init__(self, address, device, queueSize = 0):
        Neuro.__init__(self, address, device)
        self.queueSize = queueSize
        self.listener = None
        self.socket = None
        self.queues = {}
        self.clients = {}
        self.queuesLock = RLock()
        self.clientsLock = RLock()
        self.watching = Event()
        self.terminate = Event()
        self.terminate.clear()
        self.watching.clear()
        self.lastSeq = -1
    
    def open(self):
        if self.listener is None:
            self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener.bind(self.address)
            self.listener.listen(1)
    
    def getQueues(self, client = None):
        self.queuesLock.acquire()
        try:
            if client is None:
                return self.queues.copy()
            else:
                return self.queues[client]
                
        finally:
            self.queuesLock.release()
    
    def setQueues(self, client, queue):
        self.queuesLock.acquire()
        try:
            self.queues[client] = queue
        finally:
            self.queuesLock.release()
        
    def registerClient(self, role, header, watching, ThreadClass, sock):
        self.clientsLock.acquire()
        try:
            if len(self.clients) == 0:
                clId = 0
            else:
                clId = max(self.clients)+1
            if role == 'EEG':
                self.setQueues(clId, Queue(self.queueSize))
            thread = ThreadClass(clId, self)
            self.clients[clId] = [role, header, watching, thread, sock]
            thread.start()
            return clId
        finally:
            self.clientsLock.release()
    
    def getRole(self, clId):
        self.clientsLock.acquire()
        try:
            return self.clients[clId][0]
        finally:
            self.clientsLock.release()
    
    def getHeader(self, clId):
        self.clientsLock.acquire()
        try:
            return self.clients[clId][1]
        finally:
            self.clientsLock.release()
    
    def getWatching(self, clId):
        self.clientsLock.acquire()
        try:
            return self.clients[clId][2]
        finally:
            self.clientsLock.release()
    
    def isWatching(self, clId):
        self.clientsLock.acquire()
        try:
            return len(self.clients[clId][2]) > 0
        finally:
            self.clientsLock.release()
            
    def getThread(self, clId):
        self.clientsLock.acquire()
        try:
            return self.clients[clId][3]
        finally:
            self.clientsLock.release()
    
    def getWatchers(self, clId):
        self.clientsLock.acquire()
        try:
            retArr = []
            for id in self.clients:
                if clId in self.getWatching(id):
                    retArr.append(id)
            return retArr
        finally:
            self.clientsLock.release()
    
    def getSocket(self, clId):
        self.clientsLock.acquire()
        try:
            return self.clients[clId][4]
        finally:
            self.clientsLock.release()
    
    def setRole(self, clId, value):
        self.clientsLock.acquire()
        try:
            self.clients[clId][0] = value
            if value == 'EEG':
                self.setQueues(clId, Queue(self.queueSize))
        finally:
            self.clientsLock.release()
    
    def setHeader(self, clId, value):
        self.clientsLock.acquire()
        try:
            self.clients[clId][1] = value
        finally:
            self.clientsLock.release()
    
    def setWatching(self, clId, value):
        self.clientsLock.acquire()
        try:
            self.clients[clId][2] = value
        finally:
            self.clientsLock.release()
    
    def isWatchingAny(self):
        self.clientsLock.acquire()
        try:
            for val in self.clients.values():
                if len(val[2]) > 0:
                    return True
            return False
        finally:
            self.clientsLock.release()
    
    def getClientsForRole(self, role):
        self.clientsLock.acquire()
        try:
            dead = []
            for id in self.clients:
                thread = self.getThread(id)
                if thread is None or not thread.isAlive():
                    if thread is not None:
                        print "Client #{0} found dead. Cleaning up..".format(id)
                    dead.append(id)
            retArr = []
            for id,val in self.clients.items():
                if id in dead:
                    val[:] = [None, None, [], None, None]
                    for cl in self.getWatchers(id):
                        self.getWatching(cl).remove(id)
                else:
                    if self.getRole(id) == role:
                        retArr.append(id)
            return retArr
        finally:
            self.clientsLock.release()
    
    def getStatus(self):
        self.clientsLock.acquire()
        try:
            dead = []
            for id in self.clients:
                thread = self.getThread(id)
                if thread is None or not thread.isAlive():
                    if thread is not None:
                        print "Client #{0} found dead. Cleaning up.".format(id)
                    dead.append(id)
            nClients = 0
            clientList = []            
            for id,val in self.clients.items():
                if id in dead:
                    val[:] = [None, None, [], None, None]
                    for cl in self.getWatchers(id):
                        self.getWatching(cl).remove(id)
                else:
                    nClients += 1
                    clientList.append('{0}:{1}'.format(id, self.getRole(id) ))
            clientList.insert(0, '{0} clients connected'.format(nClients))
            return '\r\n'.join(clientList)
        finally:
            self.clientsLock.release()
    
    def recvCommands(self, clId):
        #Note: this is crap, it should be rewritten soon
        reW = re.compile(r"^(un)?watch\s+([0-9]+)")
        reH = re.compile(r"^getheader\s+([0-9]+)")
        reD = re.compile(r"^!(\s+[0-9]+)+")
        reS = re.compile(r"^setheader\s(.*)")
        sock = self.getSocket(clId)
        lines = self.recv(sock).splitlines()
        if len(lines) == 0:
            raise NeuroError("No commands received. Is socket opened?")
        messages = []
        for msg in lines:
            mW = reW.match(msg)
            mH = reH.match(msg)
            mD = reD.match(msg)
            mS = reS.match(msg)
            if msg.strip() == 'display':
                print "Client #{0} issued 'display' command.".format(clId)
                self.setRole(clId, "Display")
                self.send("200 OK", sock)
            elif msg.strip() == 'eeg':
                print "Client #{0} issued 'eeg' command.".format(clId)
                self.setRole(clId, "EEG")
                self.send("200 OK", sock)
            elif msg.strip() == 'status':
                print "Client #{0} issued 'status' command.".format(clId)
                #self.send("200 OK", sock)
                self.send("200 OK\r\n"+self.getStatus(), sock) # brainbay cannot recognize if it is separated
            elif msg.strip() == 'role':
                print "Client #{0} issued 'role' command.".format(clId)
                self.send(self.getRole(clId), sock)
            elif mW is not None:
                target = int(mW.group(2))
                if self.getRole(clId) != "Display" or  self.getRole(target) != 'EEG':
                    if mW.group(1) == 'un':
                        print "Client #{0} issued 'unwatch' command but not in display role or target is not EEG.".format(clId)
                    else:
                        print "Client #{0} issued 'watch' command but not in display role or target is not EEG.".format(clId)
                    self.send('400 BAD REQUEST', sock)
                else:
                    self.send("200 OK", sock)
                    if mW.group(1) == 'un':
                        print "Client #{0} issued 'unwatch {1}' command.".format(clId, target)
                        #print "target={0} watching={1}".format(target, self.getWatching(clId))
                        self.getWatching(clId).remove(target)
                    else:
                        print "Client #{0} issued 'watch {1}' command.".format(clId, target)
                        self.getWatching(clId).append(target)
            elif mH is not None:
                target = int(mH.group(1))
                if self.getRole(clId) != "Display" or  self.getRole(target) != 'EEG':
                    print "Client #{0} issued 'getheader' command but not in display role or target is not EEG.".format(clId)
                    self.send('400 BAD REQUEST', sock)
                else:
                    print "Client #{0} issued 'getheader {1}' command.".format(clId, target)
                    #self.send("200 OK", sock)
                    self.send("200 OK\r\n"+self.getHeader(target), sock)
            elif mS is not None:
                self.setHeader(clId, mS.group(1))
                print "Client #{0} issued 'setheader' command. Header is now <{1}>.".format(clId, self.getHeader(clId))
                self.send("200 OK", sock)
            elif mD is not None:
                if len(self.getWatchers(clId)) > 0:
                    msg = msg.split()
                    msg.insert(1, str(clId))
                    messages.append(' '.join(msg))
                self.send("200 OK", sock)
            else:
                print "Client #{0} issued unrecognized command.\n{1}".format(clId,msg)
                self.send('400 BAD REQUEST', sock)
        if self.getRole(clId) == 'EEG':
            self.getQueues(clId).put('\r\n'.join(messages))

    def recvData(self, clId):
        data = []
        sock = self.getSocket(clId)
        for packet in sock.getData():
            if self.lastSeq > -1 and self.lastSeq + 1 != packet[0]:
                #raise NeuroError("Sequence number not consistent.")
                print "Sequence number not consistent."
            self.lastSeq = packet[0]
            if packet[1] + 2 != len(packet):
                raise NeuroError("Packet size not consistent.")
            s = "".join([ " {"+str(i+3)+"}" for i in range(packet[1]) ])
            data.append(("! {0} {1} {2}" + s).format(clId, *packet))
        return "\r\n".join(data)
    
    def cleanup(self):
        print "Trying to shutdown gracefully."
        self.watching.clear()
        self.terminate.set()
        
        #print self.consumer.name
        self.consumer.join()
        for id in self.clients:
            thread = self.getThread(id)
            if thread is not None and thread.isAlive():
                #print thread.name
                thread.join()
        
        self.listener.shutdown(0)
        self.listener.close()
        for id in self.clients:
            sock = self.getSocket(id)
            if sock is not None and not isinstance(sock,NeuroDevice):
                sock.shutdown(0)
                sock.close()
    
    def run(self):
        Neuro.run(self)
        clId = self.registerClient('EEG', self.device.getHeader(), [], NeuroDeviceProducer, self.device)
        self.consumer = NeuroSocketConsumer(clId, self)
        self.consumer.start()
        print "Server is going to accept connections on address {0}:{1}.".format(*self.address)
        while True:
            try:
                sock, addr =  self.listener.accept()
                sock.settimeout(10)
                clId = self.registerClient('Unknown', '', [], NeuroSocketCommander, sock)
                print "Connected client #{0} from {1}:{2}.".format(clId, *addr)
            except KeyboardInterrupt:
                print "Received interupt signal."
                self.cleanup()
                raise
            except Exception as e:
                self.cleanup()
                raise
        

