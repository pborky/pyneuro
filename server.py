
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
        self.name = "DeviceThread-{}".format(clId)
        self.daemon = True
    
    def run(self):
        while not self.caller.terminate.isSet():
            self.caller.watching.wait(1.0)
            if not self.caller.watching.isSet():
                continue
            try:
                self.queue.put(self.caller.recvData(self.clId),1.0)
            except Full:
                raise NeuroError("Queue busy. Dropping packet(s).")
            
class NeuroSocketCommander(Thread):
    def __init__(self, clId, caller):
        threading.Thread.__init__(self)
        self.clId = clId
        self.caller = caller
        self.name = "CommanderThread-{}".format(clId)
        self.daemon = True
    
    def run(self):
        while not self.caller.terminate.isSet():
            try:
                self.caller.recvCommands(self.clId)
            except NeuroTimeout as e:
                #print "*** Oops! Got: {}".format(e)
                pass
            except NeuroError as e:
                print "*** Oops! {} got: {}".format(threading.currentThread().name, e)
                break
            self.caller.getClientsForRole('Display')
            if self.caller.isWatchingAny():
                self.caller.watching.set()
            else:
                self.caller.watching.clear()

class NeuroSocketConsumer(Thread):
    def __init__(self, clId, caller):
        threading.Thread.__init__(self)
        self.clId = clId
        self.caller = caller
        self.queue = caller.getQueues(clId)
        self.name = "SenderThread-{}".format(clId)
        self.daemon = True
    
    def run(self):
        while not self.caller.terminate.isSet():
            if self.queue.empty():
                continue
            self.caller.getClientsForRole('EEG')
            watchers = self.caller.getWatchers(self.clId)
            try: 
                packet = self.queue.get(1.0)
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
                    print "*** Oops! {} got: {}".format(threading.currentThread().name, e)

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
                q = self.queues.copy()
            else:
                q = self.queues[client]
        finally:
            self.queuesLock.release()
        return q

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
                        print "Client #{} found dead. Cleaning up..".format(id)
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
                        print "Client #{} found dead. Cleaning up.".format(id)
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
                    clientList.append('{}:{}'.format(id, self.getRole(id) ))
            clientList.insert(0, '{} clients connected'.format(nClients))
            return '\r\n'.join(clientList)
        finally:
            self.clientsLock.release()
    
    def recvCommands(self, clId):
        reW = re.compile(r"^(un)?watch\s+([0-9]+)")
        reH = re.compile(r"^getheader\s+([0-9]+)")
        sock = self.getSocket(clId)
        lines = self.recv(sock).splitlines()
        if len(lines) == 0:
            raise NeuroError("No commands received. Is socket opened?")
        for msg in lines:
            mW = reW.match(msg)
            mH = reH.match(msg)
            if msg.strip() == 'display':
                print "Client #{} issued 'display' command.".format(clId)
                self.setRole(clId, "Display")
                self.send("200 OK", sock)
            elif msg.strip() == 'status':
                print "Client #{} issued 'status' command.".format(clId)
                self.send("200 OK", sock)
                self.send(self.getStatus(), sock)
            elif msg.strip() == 'role':
                print "Client #{} issued 'role' command.".format(clId)
                self.send(self.getRole(clId), sock)
            elif mW is not None:
                target = int(mW.group(2))
                if self.getRole(clId) != "Display" or  self.getRole(target) != 'EEG':
                    if mW.group(1) == 'un':
                        print "Client #{} issued 'unwatch' command but not in display role or target is not EEG.".format(clId)
                    else:
                        print "Client #{} issued 'watch' command but not in display role or target is not EEG.".format(clId)
                    self.send('400 BAD REQUEST', sock)
                else:
                    self.send("200 OK", sock)
                    if mW.group(1) == 'un':
                        print "Client #{} issued 'unwatch' command.".format(clId)
                        self.getWatching(clId).remove(target)
                    else:
                        print "Client #{} issued 'watch' command.".format(clId)
                        self.getWatching(clId).append(target)
            elif mH is not None:
                target = int(mH.group(1))
                if self.getRole(clId) != "Display" or  self.getRole(target) != 'EEG':
                    print "Client #{} issued 'getheader' command but not in display role or target is not EEG.".format(clId)
                    self.send('400 BAD REQUEST', sock)
                else:
                    print "Client #{} issued 'getheader' command.".format(clId)
                    self.send("200 OK", sock)
                    self.send(self.getHeader(target), sock)
            else:
                print "Client #{} issued unrecognized command.".format(clId)
                self.send('400 BAD REQUEST', sock)

    def recvData(self, clId):
        data = []
        sock = self.getSocket(clId)
        for packet in sock.getData():
            if self.lastSeq > -1 and self.lastSeq + 1 != packet[0]:
                raise NeuroError("Sequence number not consistent.")
            self.lastSeq = packet[0]
            if packet[1] + 2 != len(packet):
                raise NeuroError("Packet size not consistent.")
            data.append(("! {} {} {}" + " {}"*(packet[1])).format(clId, *packet))
        return "\r\n".join(data)
    
    def cleanup(self):
        print "Trying to shutdown gracefully."
        self.watching.clear()
        self.terminate.set()
        
        self.consumer.join()
        for id in self.clients:
            thread = self.getThread(id)
            if thread is not None and thread.isAlive():
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
        print "Server is going to accept connections on address {}:{}.".format(*self.address)
        while True:
            try:
                sock, addr =  self.listener.accept()
                sock.settimeout(10)
                clId = self.registerClient('Unknown', None, [], NeuroSocketCommander, sock)
                print "Connected client #{} from {}:{}.".format(clId, *addr)
            except KeyboardInterrupt:
                print "Received interupt signal."
                self.cleanup()
                raise
            except Exception as e:
                self.cleanup()
                raise
        

