
import socket

from usbhelpers import findUSBEndpoints
from usb.core import Endpoint,Interface
from usb.util import endpoint_direction,ENDPOINT_IN,ENDPOINT_OUT

from header import Header

#from server import NeuroServer
#from client import NeuroClientEEG,NeuroClientDisp

DEFAULT_PORT = 8336
DEFAULT_HOST = "localhost"

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

