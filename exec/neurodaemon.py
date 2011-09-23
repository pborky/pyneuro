#!/usr/bin/python

def parseArgs(argv, defaultAddress = None):
    try:
        if len(sys.argv) == 1 and defaultAddress is not None:
            return ('listen', defaultAddress)
        if len(sys.argv) < 3:
            return None
        behavior = 'listen'
        if sys.argv[1] == '-c':
            behavior = 'connect'
            host = sys.argv[2]
            port = int(sys.argv[3])
        elif sys.argv[1] == '-l':
            host = sys.argv[2]
            port = int(sys.argv[3])
        else:
            host = sys.argv[1]
            port = int(sys.argv[2])
        return (behavior, (host, port))
    except:
        return None



if __name__ == "__main__":
    import sys
    import pyneuro
    from pyneuro import NeuroError,NeuroDeviceError
    from pyneuro.server import NeuroServer
    from pyneuro.client import NeuroClientEEG
    from pyneuro.niadevice import NIADevice
    from pyneuro.trigger import TriggerDevice

    NEURO = { 'listen': NeuroServer, 'connect': NeuroClientEEG }

    args = parseArgs(sys.argv, (pyneuro.DEFAULT_HOST, pyneuro.DEFAULT_PORT))
    
    if args is None:
        print '''Usage:

pynia.py [[<options>] <host> <port>]
where: 
    <host> is address of neuroserver`s host (defaults to {0})
    <port> is port on which neuroserver is listenning (defaults to {1})
    <options> are:
        -l start lightweight NeuroServer and listen (default)
        -c connect to another NeuroServer
'''.format(pyneuro.DEFAULT_HOST, pyneuro.DEFAULT_PORT)
        exit(1)
    
    address = args[1]
    NeuroClass = NEURO[args[0]]
    
    try:
        # instantionate objects: nia device and socket
        try:
            dev = NIADevice()
            print "NIA device has been found."
        except NeuroDeviceError:
            print "NIA device has not been found. Using dummy trigger device."
            dev = TriggerDevice(4000)
        neuro = NeuroClass(address, dev)
        if NeuroClass == NeuroServer:
            print "Starting NeuroServer."
        else:
            print "Starting NeuroClient."
        neuro.run()
        
    except NeuroError as err:
        print "*** Oops! Got error: {0}".format(err)
    except KeyboardInterrupt:
        print "Shut down on user demand."

