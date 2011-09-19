#!/usr/bin/python
# Based on http://code.google.com/p/pynia/

import sys
import usb
import numpy
import threading
import time

from threading import Semaphore,Thread

import pyneuro
from pyneuro import NeuroError
from pyneuro.client import NeuroClientDisp,NeuroClientEEG
from pyneuro.trigger import TriggerDevice

class NIA_Interface():
    """ Attaches the NIA device, and provides low level data collection and information
    """
    def __init__(self,address):
        self.address = address
        self.QUEUE_SIZE = 40

    def open(self) :
        """ Attache NeuroClient
        """
        try:
            print "Openning connection to neuroserver instance at {0}:{1}.".format(*self.address)
            self.client = NeuroClientDisp(self.address, self.QUEUE_SIZE)
            self.client.run()
            self.client.watch(0)
        except usb.USBError, err:
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
            data = [ (i + 32768) * 256 for i in  data[0] ]
        else:
            data = []
        return data
        
class NIA_Data():
    """ Looks after the collection and processing of NIA data
    """
    def __init__(self,point,address) :
        self.Points = point # there is a point every ~2 ms, 
        self.Working_Data = []
        self.Hamming = numpy.hamming(256)
        self.interface = NIA_Interface(address)
        self.interface.open()
        self.Fourier_Image = numpy.zeros((80,500), dtype=numpy.int8)
        sigmoid = 1/(1 + numpy.exp(-8+0.25*numpy.arange(128)))
        self.Sigmoid_Filter = numpy.concatenate((sigmoid,sigmoid[::-1]))
        self.REM_interval = 40
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
        self.REM_min = 1
        self.REM_max = 1
        self.REM_period = 0
                 
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
        numpy.std(self.Processed_Data)
        self.Frequencies = abs(filtered)[5:45]
    
    def isREM(self):
        """Check for EOG activity for over x seconds
        """
        current_std = numpy.std(self.Processed_Data)
        if current_std >= self.REM_min:
            if current_std <= self.REM_max:
                self.REM_period += 1
                if self.REM_period == self.REM_interval:
                    self.REM_period = 0
                    return True
                else:
                     return False
            else:
                 self.REM_period = 0
                 return False             
        else:            
            self.REM_period = 0
            return False
        
    def waveform(self):
        """Generate waveform data for OpenGL
        """
        data = numpy.array(nia.Processed_Data, float)
        avg = numpy.average(data)
        x_max = avg+0.2
        x_min = avg-0.2
        data = (100*((data-x_min)/(x_max-x_min)))
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

class TriggerThread(Thread):
    def __init__(self, trigger):
        Thread.__init__(self)
        self.triggerClient = trigger
        self.name = "TriggerDeviceThread"
        self.daemon = True

    def run(self):
        self.triggerClient.run()

if __name__ == "__main__":
    
    address = parseArgs(sys.argv, (pyneuro.DEFAULT_HOST, pyneuro.DEFAULT_PORT))

    trg = TriggerDevice(64)
    cl = NeuroClientEEG(address, trg)
    t = TriggerThread(cl)    
    t.start()
    
    import pyglet
    import simplui
    import urllib
    from xml.dom import minidom
    
    window = pyglet.window.Window(width=700, height=280, caption='TweetDreams')
    frame = simplui.Frame(0, 0, 700, 280, simplui.Theme('themes/macos/theme.json')) 
    window.push_handlers(frame)
    interval = 4.0
    timer = 15.0
    in_seconds = int(60*timer)
    start_time = 0
    ft = pyglet.font.load('Arial', 20)
    fps_text = pyglet.font.Text(ft, y=50)
    
    
    nia = NIA_Data(25, address)
   
    semaphore = Semaphore()
    collector = Collector(nia, semaphore)
    
    print "Starting collector worker."
    collector.start()

    scale = [x for x in range(992)]
    pic_cols = [2*x for x in range(256)]
    vertex_list = pyglet.graphics.vertex_list(len(scale)/2, ('v2i', scale))  

    def calibration(button):
    	window.clear()
    	ft = pyglet.font.load('Arial', 20)
        fps_text = pyglet.font.Text(ft, x=10, y=100)
    	fps_text.text = ("Calibration in Progress, remain calm and still.") 
    	fps_text.draw()   
    	window.flip()
        time.sleep(2)
    	nia.calibrate()
    	normal = numpy.std(nia.Processed_Data)    	
    	ft = pyglet.font.load('Arial', 20)
        fps_text = pyglet.font.Text(ft, x=10, y=60)
    	fps_text.text = ("Close eyes, and simulate REM for 5 seconds") 
    	fps_text.draw()   
    	window.flip()    	
    	time.sleep(2)
        nia.calibrate()
        simulated_REM = numpy.std(nia.Processed_Data)
        if simulated_REM >= normal*4:
            ft = pyglet.font.load('Arial', 20)
            fps_text = pyglet.font.Text(ft, x=10, y=20)
    	    fps_text.text = ("Calibration Complete") 
    	    fps_text.draw()
    	    nia.REM_min = simulated_REM*0.5
    	    nia.REM_max = simulated_REM*1.5
    	else:
            ft = pyglet.font.load('Arial', 20)
            fps_text = pyglet.font.Text(ft, x=10, y=20)
    	    fps_text.text = ("Calibration Failed, please try again") 
    	    fps_text.draw()   	        
    	window.flip()
    	time.sleep(5)
    	window.clear()

    def interval_action(slider):
        global interval
    	interval = slider.value
    	nia.REM_interval = round(slider.value, 1)*10
    	
    def timer_action(slider):
        global timer
        timer = slider.value
        in_seconds = int(60*timer)	

    def check_action(checkbox):
        global start_time
        start_time = time.clock() + in_seconds

    def PostUpdate(u,p,d,t):
        post = {'status':d}
        post = urllib.urlencode(post)
        url = 'http://'+u.replace('@','%40')+':'+p+'@twitter.com/statuses/'+'update.xml'
        resp = urllib.urlopen(url,post).read()
        if t:
            parseresponse(resp,d)

    def parseresponse(xml,status):
      """ Check Twitter Responce
      """
      xmldata = minidom.parseString(xml)
      text = xmldata.getElementsByTagName('text')[0].firstChild.data
      if text == status.strip():
          element = frame.get_element_by_name('messages')
          element.add( simplui.Label(20, 20, 'Twitter Successfully Sent') )
      else: 
          element = frame.get_element_by_name('messages')
          element.add( simplui.Label(20, 20, 'Twitter Failed!') )
          
    def add_Message(button):
    	if frame.get_element_by_name('password').text == "password":
    	    if frame.get_element_by_name('user').text == "user":
    	        element = frame.get_element_by_name('messages')
                element.add( simplui.Label(20, 20, 'Enter username/password') )
    	else:
    	    PostUpdate(frame.get_element_by_name('user').text,frame.get_element_by_name('password').text,'Testing TweetDreams', True)
    	    
    	    

    	
    frame.add( simplui.Dialogue(500, 0, 200, 256, 'pyNIA Interface', content=
    	simplui.VerticalLayout(0, 0, 200, 100, padding=5, children=[
    		simplui.FoldingBox(0, 0, 200, 140, 'pyNIA Settings', content=
    			simplui.VerticalLayout(0, 0, 200, 300, children=[
    				simplui.Label(20, 20, 'Detection Interval:', name='seconds'),
    				simplui.Slider(20, 40, 160, min=3.0, max=10.0, value=1.0, action=interval_action),
    				simplui.Label(20, 20, 'Startup Timer:', name='minutes'),
    				simplui.Slider(20, 40, 160, min=15.0, max=90.0, value=0.0, action=timer_action),
    				simplui.Button(20, 80, 80, 20, 'Calibration', action=calibration)
    				])
    			),
    		simplui.FoldingBox(0, 0, 200, 100, 'Twitter Settings', collapsed = True, content=
    			simplui.VerticalLayout(0, 0, 200, 300, name='misc_layout', children=[
    				simplui.TextInput(20, 80, 160, text='user', name='user'),
    				simplui.TextInput(20, 80, 160, text='password', name='password'),
    				simplui.Button(20, 80, 80, 20, 'test connection', action=add_Message),
    				simplui.Label(20, 20, 'Twitter Message:'),
    				simplui.TextInput(20, 80, 160, text='is Dreaming', name='tweet'),
    				simplui.Checkbox(20, 60, 'Active', name='active', action=check_action)
    				])
    			),   			

    		simplui.FoldingBox(0, 0, 200, 100, 'Messages', collapsed = False, content=
    			simplui.VerticalLayout(0, 0, 200, 300, name='messages')
    			)
    		])
    	) )    	

    def update(x):
        if not collector.isAlive():
            raise Exception("Collector worker found dead.")

        global start_time
        window.clear()
        
        nia.process()
        if nia.isREM():            
            if frame.get_element_by_name('active').value:
                if time.clock() >= start_time:
                    PostUpdate(frame.get_element_by_name('user').text,frame.get_element_by_name('password').text,(frame.get_element_by_name('tweet').text + time.strftime(" at %H:%M:%S", time.gmtime())), False)
                    element = frame.get_element_by_name('messages')
                    element.add( simplui.Label(20, 20, time.strftime("REM Tweeted at %H:%M:%S", time.gmtime())) )
                    start_time = time.clock() + in_seconds
            else:
                element = frame.get_element_by_name('messages')
                element.add( simplui.Label(20, 20, time.strftime("REM Detected at %H:%M:%S", time.gmtime())) )
            trg.setValues((255,))
        else:
            trg.setValues((127,))
        data = nia.fourier_image()
        image = pyglet.image.ImageData(500,80,'I', data)
        image.blit(0,0)

        data = nia.waveform()
        vertex_list.vertices = data
        vertex_list.draw(pyglet.gl.GL_LINES)
        
        element = frame.get_element_by_name('seconds')
        element.text = 'Detection Interval: %.1fs' % (interval)
        element = frame.get_element_by_name('minutes')
        element.text = 'Startup Timer: %.1fm' % (timer)        
        frame.draw()

        semaphore.release()
     
    pyglet.clock.schedule(update)
    try:
        pyglet.app.run()
    except Exception as e:
        print "Oops!! {0} got: {1}".format(threading.currentThread().name, e)

