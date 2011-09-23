
import usb.core
from usb.core import Endpoint,Interface
from usb.util import endpoint_direction,ENDPOINT_IN,ENDPOINT_OUT

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
