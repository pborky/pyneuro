#!/usr/bin/python

''' Based on pyNIA http://code.google.com/p/pynia/
'''
import sys
import numpy
import threading

from threading import Semaphore,Thread

import pyneuro
from pyneuro import NeuroError
from pyneuro.client import NeuroClientDisp

class NIA_Interface():
    """ Attaches the NIA device, and provides low level data collection and information
    """
    def __init__(self,address):
        self.address = address
        self.QUEUE_SIZE = 40

    def open(self) :
        """ Attach NeuroClient 
        """
        try:
            print "Openning connection to neuroserver instance at {0}:{1}.".format(*self.address)
            self.client = NeuroClientDisp(self.address, self.QUEUE_SIZE)
            self.client.run()
            self.client.watch(0)
        except Exception, err:
            print >> sys.stderr, err
    
    def close(self):
        """ Release NIA interface
        """
        try:
            self.client.unwatch(0)
        except Exception, err:
            print >> sys.stderr, err
    
    def read(self, points):
        """ Read data off the NIA from its internal buffer of up to 16 samples
        """
        data = self.client.getData(0, 10*points)
        if len(data) > 0:
            data =  [ (i + 32768) * 256 for i in  data[0] ]
        else:
            data = []
        return data
        
class NIA_Data():
    """ Looks after the collection and processing of NIA data
    """
    def __init__(self,point,address) :
        self.Points = point # there is a point every ~5 ms, 
        self.Working_Data = []
        self.Hamming = numpy.hamming(256)
        self.interface = NIA_Interface(address)
        self.interface.open()
        self.Fourier_Image = numpy.zeros((80,500), dtype=numpy.int8)
        sigmoid = 1/(1 + numpy.exp(-8+0.25*numpy.arange(128)))
        self.Sigmoid_Filter = numpy.concatenate((sigmoid,sigmoid[::-1]))
        self.calibrate()
        
    def calibrate(self):
        """Perform a NIA Calibration"""
        for i in range(100):
            self.record()
        self.Calibration = sum(self.Working_Data)/len(self.Working_Data)
        fourier_stack = numpy.zeros((20,40), dtype=float)
        for i in range(20):
            self.record()
            self.process()
            fourier_stack[i,:] = self.Frequencies
        self.Fourier_Calibration = numpy.average(fourier_stack,0)   
                 
    def record(self):
        """ This function is called via threading, so that pyglet can plot the
        previous set of data whist this function collects the new data. It
        sorts out the data into a list of the last seconds worth of data (3840 
        samples, about 1.5 percent less than actual, but close enough). 4 extra
        data points are taken for smoothing.
	    """   
        current_data = self.interface.read(self.Points)
        self.Working_Data = (self.Working_Data+current_data)[-3845:-1] 
    
    def process(self):
        """ Process collected data into denoised and Fourier transformed data.
        """
        filtered = numpy.fft.fft(map(lambda v,w,x,y,z: (v+2*w+3*x+2*y+z)/(
                9.0-self.Calibration), self.Working_Data[0:-4],self.Working_Data[1:-3], 
                self.Working_Data[2:-2], self.Working_Data[3:-1], 
                self.Working_Data[4:])[::15]*self.Hamming)*self.Sigmoid_Filter
        self.Processed_Data = (numpy.fft.ifft(filtered)/self.Hamming)[3:253]
        self.Frequencies = abs(filtered)[5:45]
        
    def waveform(self):
        """Generate waveform data for OpenGL
        """
        data = numpy.array(nia.Processed_Data, float)
        avg = numpy.average(data)
        x_max = avg+0.2
        x_min = avg-0.2
        data = (100*((data-x_min)/(x_max-x_min))) #normalise with a bit of a window 
        data = data + 180 - numpy.average(data)
        data[data<80] = 80
        data[data>280] = 280
        data = list(data)
        scale = []

        scale.append(pic_cols[0])
        scale.append(int(data[0]))
        for i in range(1,248):
            scale.append(pic_cols[i])
            scale.append(int(data[i]))
            scale.append(pic_cols[i])
            scale.append(int(data[i]))
        scale.append(pic_cols[249])
        scale.append(int(data[249]))
        return scale  

    def fourier_image(self):
        """Generate Fourier Spectrogram
        """
        self.Fourier_Image[:,0:499] = self.Fourier_Image[:,1:500]
        next_line = self.Frequencies/self.Fourier_Calibration
        
        x_max = max(next_line)
        x_min = min(next_line)
        next_line = (255*(next_line-x_min)/(x_max-x_min))
        y = numpy.vstack((next_line,next_line))
        y = numpy.ravel(y,'F')
        self.Fourier_Image[:,499] = y
        return self.Fourier_Image.tostring()

    def fingers(self):
        """Returns 6 BrainFinger Values
        """
        fingers = []
        waves = (6,9,12,15,20,25,30)
        for i in range(6):
            fingers.append((sum(self.Frequencies[waves[i]:waves[i+1]])/100))
        return fingers    

class Collector(Thread):
    def __init__(self, data, semaphore):
        Thread.__init__(self)
        self.data = data
        self.semaphore = semaphore
        self.name = "CollectorThread"
        self.daemon = True
    
    def run(self):
        while True:
            semaphore.acquire()
            try:
                self.data.record()
            except Exception as e:
                print "Oops!! {0} got: {1}".format(threading.currentThread().name, e)
                break

def parseArgs(argv, defaultAddress = None):
    try:
        if len(sys.argv) == 1 and defaultAddress is not None:
            return defaultAddress
        if len(sys.argv) < 3:
            return None
        host = sys.argv[1]
        port = int(sys.argv[2])
        return (host, port)
    except:
        return None

if __name__ == "__main__":
    address = parseArgs(sys.argv, (pyneuro.DEFAULT_HOST, pyneuro.DEFAULT_PORT))
    if address is None:
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

    import pyglet
    nia = NIA_Data(5, address)
    semaphore = Semaphore()
    collector = Collector(nia, semaphore)
    print "Starting collector worker."
    collector.start()

    window = pyglet.window.Window(width=500, height=280)
    #backgound = pyglet.image.load('pynia.png')
    #step = pyglet.image.load('step.png')

    scale = [x for x in range(992)]
    pic_cols = [2*x for x in range(256)]
    vertex_list = pyglet.graphics.vertex_list(len(scale)/2, ('v2i', scale))

    @window.event
    def on_key_press(symbol, modifiers):
        nia.calibrate()

    def update(x):
        if not collector.isAlive():
            raise Exception("Collector worker found dead.")
        
        window.clear()
        
        nia.process()
        
        data = nia.fourier_image()
        image = pyglet.image.ImageData(500,80,'I', data)
        image.blit(0,0)
        
        data = nia.waveform()
        vertex_list.vertices = data
        vertex_list.draw(pyglet.gl.GL_LINES)
        
        #print nia.fingers()
        
        semaphore.release()
    
    pyglet.clock.schedule(update)
    try:
        pyglet.app.run()
    except Exception as e:
        print "Oops!! {0} got: {1}".format(threading.currentThread().name, e)
 
            
