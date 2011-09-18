#!/bin/env python

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
    from common import NeuroError
    from client import NeuroClientEEG
    from server import NeuroServer,DEFAULT_HOST,DEFAULT_PORT
    from niadevice import NIAError,NIADevice

    NEURO = { 'listen': NeuroServer, 'connect': NeuroClientEEG }

    args = parseArgs(sys.argv, (DEFAULT_HOST, DEFAULT_PORT))
    
    if args is None:
        print '''Usage:

pynia.py [[<options>] <host> <port>]
where: 
    <host> is address of neuroserver`s host (defaults to {})
    <port> is port on which neuroserver is listenning (defaults to {})
    <options> are:
        -l start lightweight NeuroServer and listen (default)
        -c connect to another NeuroServer
'''.format(DEFAULT_HOST, DEFAULT_PORT)
        exit(1)
    
    address = args[1]
    NeuroClass = NEURO[args[0]]
    
    try:
        # instantionate objects: nia device and socket
        nia = NIADevice()
        neuro = NeuroClass(address, nia)
        if NeuroClass == NeuroServer:
            print "Starting NeuroServer."
        else:
            print "Starting NeuroClient."
        neuro.run()
        
    except NIAError as err:
        print "*** Oops! NIADevice error: {0}".format(err)
    except NeuroError as err:
        print "*** Oops! NeuroServer error: {0}".format(err)
    except KeyboardInterrupt:
        print "Shut down on user demand."

