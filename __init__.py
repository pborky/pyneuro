
import socket
import usb.core
from usb.core import Endpoint,Interface
from usb.util import endpoint_direction,ENDPOINT_IN,ENDPOINT_OUT

#from server import NeuroServer
#from client import NeuroClientEEG,NeuroClientDisp

DEFAULT_PORT = 8336
DEFAULT_HOST = "localhost"

def objFind(obj, leaveClass, matcher = None, find_all=False):
    r'''Find object in object tree
    obj - root of the tree
    leaveClass - leave of the tree is of class leaveClass
    matcher - matcher function that yields True of False
    '''
    if find_all:
        retArray = []
        for i in obj:
            if isinstance(i, leaveClass): # object is leave
                if matcher is None or matcher(i):
                    retArray.append(i)
            else:
                retArray.extend(objFind(i, leaveClass, matcher = matcher, find_all = True))
        return retArray
    else:
        for i in obj:
            if isinstance(i, leaveClass): # object is leave
                if matcher is None or matcher(i):
                    return i
            else:
                retObj = objFind(i, leaveClass, matcher = matcher, find_all = False)
                if retObj is not None:
                    return retObj
        return None

def findUSBEndpoints(idVendor, idProduct, direction):
    r"""Finds and initializes endpoints
    At first it searches for matching device, detaches kernel drivers for all interfaces 
    and finally returns first input endpoint object.        
    """
    # get device
    dev = usb.core.find(idVendor = idVendor, idProduct = idProduct, find_all = False )
    if dev is None:
        return None
    
    # iterate over all interfaces under device and detach kernel driver
    for i in objFind( dev, Interface, find_all = True ):
        if dev.is_kernel_driver_active(i.bInterfaceNumber):
            dev.detach_kernel_driver(i.bInterfaceNumber)
        
    # match endpoint that has input direction
    matcher = lambda e: endpoint_direction(e.bEndpointAddress) == direction
    return objFind( dev, Endpoint, matcher = matcher, find_all = False )

class NeuroError(Exception):
    pass

class NeuroTimeout(NeuroError):
    pass

class NeuroDeviceError(NeuroError):
    pass

class NeuroDevice:
    def __init__(self, header):
        self.header = header
    
    def getHeader(self):
        return self.header

    def getData(self):
        raise Exception("Not implemented.")

class NeuroDeviceUSB(NeuroDevice):
    def __init__(self, idVendor, idProduct, header):
        NeuroDevice.__init__(self, header=header)
        # find USB device and input endpoint
        self.endpoint = findUSBEndpoints(idVendor, idProduct, ENDPOINT_IN)
        if self.endpoint is None:
            raise NeuroDeviceError("No USB devices or endpoints has been found.")

class Neuro:
    def __init__(self, address, device):
        #if device is not None and not isinstance(device, NeuroDevice):
        #    raise NeuroError("Parameter 'device' must be instance of 'NeuroDevice'.")
        
        self.address = address
        self.device = device
        self.socket = None
    
    def send(self, data, sock = None):
        if sock is None:
            sock = self.socket
        if sock is None:
            raise NeuroError("Socket is not open.")
        try:
            return sock.send(data+'\r\n')
        except socket.timeout:
            raise NeuroTimeout("Timeout writting to socket.")
        except socket.error as e:
            raise NeuroError("Error writting to socket: {0}".format(e))
    
    def recv(self, sock = None):
        if sock is None:
            sock = self.socket
        if sock is None:
            raise NeuroError("Socket is not open.")
        try:
            return sock.recv(4096)
        except socket.timeout:
            raise NeuroTimeout("Timeout reading socket.")
        except socket.error as e:
            raise NeuroError("Error reading socket: {0}".format(e))
    
    def run(self):
        self.open()

