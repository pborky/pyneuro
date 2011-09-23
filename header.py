
import re
import datetime

HEAD1 = [   r'(?P<version>[\x20-\x7e]{8})',
            r'(?P<patient>[\x20-\x7e]{80})',
            r'(?P<recording>[\x20-\x7e]{80})',
            r'(?P<startdate>[\x20-\x7e]{8})',
            r'(?P<starttime>[\x20-\x7e]{8})',
            r'(?P<headbytes>[\x20-\x7e]{8})',
            r'(?P<reserved>[\x20-\x7e]{44})',
            r'(?P<recordcount>[\x20-\x7e]{8})',
            r'(?P<recordduration>[\x20-\x7e]{8})',
            r'(?P<signalcount>[0-9\x20]{4})',
            r'(?P<signals>[\x20-\x7e]+)' ]

HEAD2 = [   r'(?P<label%s>[\x20-\x7e]{16})',
            r'(?P<transducer%s>[\x20-\x7e]{80})',
            r'(?P<physdim%s>[\x20-\x7e]{8})',
            r'(?P<physmin%s>[\x20-\x7e]{8})',
            r'(?P<physmax%s>[\x20-\x7e]{8})',
            r'(?P<digmin%s>[\x20-\x7e]{8})',
            r'(?P<digmax%s>[\x20-\x7e]{8})',
            r'(?P<prefilter%s>[\x20-\x7e]{80})',
            r'(?P<samplescount%s>[\x20-\x7e]{8})',
            r'(?P<reserved%s>[\x20-\x7e]{32})' ]

PATIENT = r'(?P<id>\w+)\s+(?P<sex>F|M)\s+(?P<day>[0-9]{2})-(?P<month>[a-zA-Z]{3})-(?P<year>[0-9]{4})\s+(?P<name>.+)'

RECORDING = r'Startdate\s+(?P<day>[0-9]{2})-(?P<month>[a-zA-Z]{3})-(?P<year>[0-9]{4})\s+(?P<id>\w+)\s+(?P<investigator>\w+)\s+(?P<equipment>\w+)(?:\s+(?P<other>\w+))?'

MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

class HeaderChannel(object):
    def __init__(self, id, header):
        self.id = id
        self.header = header
    @property
    def label(self):
        return self.header.headDict2['label%s' % self.id]
    @label.setter
    def label(self, value):
        self.header.headDict2['label%s' % self.id] = value
    @property
    def transducer(self):
        return self.header.headDict2['transducer%s' % self.id]
    @transducer.setter
    def transducer(self, value):
        self.header.headDict2['transducer%s' % self.id] = value
    @property
    def physicalDimension(self):
        return self.header.headDict2['physdim%s' % self.id]
    @physicalDimension.setter
    def physicalDimension(self, value):
        self.header.headDict2['physdim%s' % self.id] = value
    @property
    def physicalMin(self):
        return self.header.headDict2['physmin%s' % self.id]
    @physicalMin.setter
    def physicalMin(self, value):
        self.header.headDict2['physmin%s' % self.id] = value
    @property
    def physicalMax(self):
        return self.header.headDict2['physmax%s' % self.id]
    @physicalMax.setter
    def physicalMax(self, value):
        self.header.headDict2['physmax%s' % self.id] = value
    @property
    def digitalMin(self):
        return self.header.headDict2['digmin%s' % self.id]
    @digitalMin.setter
    def digitalMin(self, value):
        self.header.headDict2['digmin%s' % self.id] = value
    @property
    def digitalMax(self):
        return self.header.headDict2['digmax%s' % self.id]
    @digitalMax.setter
    def digitalMax(self, value):
        self.header.headDict2['digmax%s' % self.id] = value
    @property
    def prefiltering(self):
        return self.header.headDict2['prefilter%s' % self.id]
    @prefiltering.setter
    def prefiltering(self, value):
        self.header.headDict2['prefilter%s' % self.id] = value
    @property
    def samplesCount(self):
        return self.header.headDict2['samplescount%s' % self.id]
    @samplesCount.setter
    def samplesCount(self, value):
        self.header.headDict2['samplescount%s' % self.id] = value
    @property
    def samplingFrequency(self):
        if self.samplesCount is None:
            return None
        return float(self.samplesCount)/float(self.header.recordDuration)
    @samplingFrequency.setter
    def samplingFrequency(self, value):
        self.samplesCount = value*self.header.recordDuration
    def __repr__(self):
        return '<HeaderChannel "%s" (fsampl=%sHz,physDim="%s")>' % (self.label, self.samplingFrequency, self.physicalDimension
)
        

class HeaderRecording(object):
    def __init__(self, header):
        self.header = header
    @property
    def id(self):
        return self.header.headDict1['recording']['id']
    @id.setter
    def id(self, value):
        self.header.headDict1['recording']['id'] = value
    @property
    def equipment(self):
        return self.header.headDict1['recording']['equipment']
    @equipment.setter
    def equipment(self, value):
        self.header.headDict1['recording']['equipment'] = value
    @property
    def investigator(self):
        return self.header.headDict1['recording']['investigator']
    @investigator.setter
    def investigator(self, value):
        self.header.headDict1['recording']['investigator'] = value
    @property
    def startDate(self):
        return self.header.headDict1['recording']['startdate']
    @startDate.setter
    def startDate(self, value):
        self.header.headDict1['recording']['startdate'] = value
    @property
    def other(self):
        return self.header.headDict1['recording']['other']
    @other.setter
    def other(self, value):
        self.header.headDict1['recording']['other'] = value
    @property
    def plain(self):
        return self.header.headDict1['recording']
    @plain.setter
    def plain(self, value):
        self.header.headDict1['recording'] = value
    def __repr__(self):
        try:
            return '<HeaderRecording "%s" (equip="%s",startdate="%s">' % (self.id, self.equipment, self.startDate.isoformat())
        except:
            return '<HeaderRecording "%s">' % self.plain
    def text(self):
        try:
            y = self.startDate.year
            m = MONTHS[self.startDate.month-1]
            d = self.startDate.day
            if self.other is None:
                return 'Startdate {0:0>2}-{1}-{2:0>4} {3} {4} {5}'.format(d, m, y, self.id, self.investigator, self.equipment)
            else:
                return 'Startdate {0:0>2}-{1}-{2:0>4} {3} {4} {5} {6}'.format(d, m, y, self.id, self.investigator, self.equipment, self.other)
        except:
            return self.plain

class HeaderPatient(object):
    def __init__(self, header):
        self.header = header
    @property
    def id(self):
        return self.header.headDict1['patient']['id']
    @id.setter
    def id(self, value):
        self.header.headDict1['patient']['id'] = value
    @property
    def name(self):
        return self.header.headDict1['patient']['name']
    @name.setter
    def name(self, value):
        self.header.headDict1['patient']['name'] = value
    @property
    def sex(self):
        return self.header.headDict1['patient']['sex']
    @sex.setter
    def sex(self, value):
        self.header.headDict1['patient']['sex'] = value
    @property
    def birthDate(self):
        return self.header.headDict1['patient']['birthdate']
    @birthDate.setter
    def birthDate(self, value):
        self.header.headDict1['patient']['birthdate'] = value
    @property
    def plain(self):
        return self.header.headDict1['patient']
    @plain.setter
    def plain(self, value):
        self.header.headDict1['patient'] = value
    def __repr__(self):
        try:
            return '<HeaderPatient "%s" (sex="%s")>' % (self.name, self.sex)
        except:
            return '<HeaderPatient "%s">' % self.plain
    def text(self):
        try:
            y = self.birthDate.year
            m = MONTHS[self.birthDate.month-1]
            d = self.birthDate.day
            return '{0} {1} {2:0>2}-{3}-{4:0>4} {5}'.format(self.id, self.sex, d, m, y, self.name)
        except:
            return self.plain

class Header(object):
    def __init__(self, head):
        self.channels = {}
        m = re.match(r''.join(HEAD1), head)
        if m is None:
            raise ValueError('Not a valid EDF header.')
        self.headDict1 = m.groupdict()
        self.headDict1['version'] = self.headDict1['version'].strip()
        self.headDict1['patient'] = self.headDict1['patient'].strip()
        self.headDict1['recording'] = self.headDict1['recording'].strip()
        
        self.headDict1['startdate'] = self.headDict1['startdate'].strip()
        self.headDict1['starttime'] = self.headDict1['starttime'].strip()
        
        self.headDict1['headbytes'] = int(self.headDict1['headbytes'])
        self.headDict1['recordcount'] = int(self.headDict1['recordcount'])
        self.headDict1['recordduration'] = int(self.headDict1['recordduration'])
        self.headDict1['signalcount'] = int(self.headDict1['signalcount'])
        
        try:
            dt = [ int(s) for s in self.headDict1['startdate'].split('.') ]
            tm = [ int(s) for s in self.headDict1['starttime'].split('.') ]
            
            dt.reverse()
            
            if dt[0] < 85:
                dt[0] += 2000
            else:
                dt[0] += 1900
            del self.headDict1['startdate'], self.headDict1['starttime']
            self.headDict1['startdatetime'] = datetime.datetime(*(dt+tm))
        except:
            self.headDict1['startdatetime'] = None
        
        m = re.match(PATIENT, self.headDict1['patient'])
        if m is not None:
            p = m.groupdict()
            y = int(p['year'])
            m = MONTHS.index(p['month'])+1
            d = int(p['day'])
            del p['year'], p['month'], p['day']
            p['birthdate'] = datetime.date(y, m, d)
            self.headDict1['patient'] = p
        self._patient = HeaderPatient(self)
        m = re.match(RECORDING, self.headDict1['recording'])
        if m is not None:
            p = m.groupdict()
            y = int(p['year'])
            m = MONTHS.index(p['month'])+1
            d = int(p['day'])
            del p['year'], p['month'], p['day']
            p['startdate'] = datetime.date(y, m, d)
            if self.headDict1['startdatetime'] is None:
                tm = [ int(s) for s in self.headDict1['starttime'].split('.') ]
                self.headDict1['startdatetime'] = datetime.datetime(y,m,d,*tm)
                del self.headDict1['startdate'], self.headDict1['starttime']
            self.headDict1['recording'] = p
        self._recording = HeaderRecording(self)
        signals = self.headDict1['signals']
        del self.headDict1['signals']
        r = []
        for s in HEAD2:
            for i in range(self.channelCount):
                r.append(s % i)
        m = re.match(r''.join(r), signals)
        
        if m is None:
            raise ValueError('Not a valid EDF header.')
        self.headDict2 = m.groupdict()
        
        for i in range(self.channelCount):
            self.headDict2['label%s' % i] = self.headDict2['label%s' % i].strip()
            self.headDict2['transducer%s' % i] = self.headDict2['transducer%s' % i].strip()
            self.headDict2['physdim%s' % i] = self.headDict2['physdim%s' % i].strip()
            self.headDict2['prefilter%s' % i] = self.headDict2['prefilter%s' % i].strip()
            
            self.headDict2['physmin%s' % i] = int(self.headDict2['physmin%s' % i])
            self.headDict2['physmax%s' % i] = int(self.headDict2['physmax%s' % i])
            self.headDict2['digmin%s' % i] = int(self.headDict2['digmin%s' % i])
            self.headDict2['digmax%s' % i] = int(self.headDict2['digmax%s' % i])
            self.headDict2['samplescount%s' % i] = int(self.headDict2['samplescount%s' % i])
        
        for i in range(self.channelCount):
            self.channels[i] = HeaderChannel(i, self)
    
    def __repr__(self):
        try:
            pat = self.patient.name
        except:
            pat= self.patient.plain
        try:
            rec = self.recording.id
        except:
            rec= self.recording.plain
        return '<Header "%s" (patient="%s",channels=%s)>' % (rec, pat, self.channelCount)
    
    def text(self):
        y = self.datetime.year % 100
        m = self.datetime.month
        d = self.datetime.day
        h = self.datetime.hour
        mi = self.datetime.minute
        s = self.datetime.second
        
        chan = []
        for i in range(10):
            chan.append([])
        for i in range(self.channelCount):
            c = self.channels[i]
            chan[0].append('{0:<16}'.format(c.label))
            chan[1].append('{0:<80}'.format(c.transducer))
            chan[2].append('{0:<8}'.format(c.physicalDimension))
            chan[3].append('{0:<8}'.format(c.physicalMin))
            chan[4].append('{0:<8}'.format(c.physicalMax))
            chan[5].append('{0:<8}'.format(c.digitalMin))
            chan[6].append('{0:<8}'.format(c.digitalMax))
            chan[7].append('{0:<80}'.format(c.prefiltering))
            chan[8].append('{0:<8}'.format(c.samplesCount))
            chan[9].append('{0:<32}'.format(''))
        for i in range(10):
            chan[i] = ''.join(chan[i])
        chan = ''.join(chan)
        
        return '{0:<8}{1:<80}{2:<80}{3:0>2}.{4:0>2}.{13:0>2}{5:0>2}.{6:0>2}.{7:0>2}{8:<8}{9:<44}{10:<8}{11:<8}{12:<4}{14}'.format(
                self.version, 
                self.patient.text(), 
                self.recording.text(), 
                d,m,h,mi,s,
                self.headSize,
                self.reserved,
                self.recordCount,
                self.recordDuration,
                self.channelCount,
                y, chan
            )
    @property
    def version(self):
        return self.headDict1['version']
    @version.setter
    def version(self, value):
        if value == 'EDF' or value == 'EDF+':
            self.headDict1['version'] = '0'
        elif value == '0':
            self.headDict1['version'] == value
        else:
            raise ValueError('Value %s is not valid version.' % value)
    @property
    def patient(self):
        return self._patient
    @property
    def recording(self):
        return self._recording
    @property
    def datetime(self):
        if 'startdatetime' not in self.headDict1:
            return (self.headDict1['startdate'], self.headDict1['starttime'])
        return self.headDict1['startdatetime']
    @datetime.setter
    def datetime(self, value):
        if 'startdatetime' not in self.headDict1:
            return (self.headDict1['startdate'], self.headDict1['starttime'])
        return self.headDict1['startdatetime']
    @property
    def headSize(self):
        return self.headDict1['headbytes']
    @headSize.setter
    def headSize(self, value):
        self.headDict1['headbytes']
    @property
    def recordCount(self):
        return self.headDict1['recordcount']
    @recordCount.setter
    def recordCount(self, value):
        self.headDict1['recordcount']
    @property
    def recordDuration(self):
        return self.headDict1['recordduration']
    @recordDuration.setter
    def recordDuration(self, value):
        self.headDict1['recordduration']
    @property
    def channelCount(self):
        return self.headDict1['signalcount']
    @channelCount.setter
    def channelCount(self, value):
        if self.headDict1['signalcount'] < value:
            for i in range(self.headDict1['signalcount'], value):
                self.channels[i] = HeaderChannel(i, self)                
                self.headDict2['label%s' % i] = 'New'
                self.headDict2['transducer%s' % i] = self.headDict2['transducer%s' % (i-1)]
                self.headDict2['physdim%s' % i] = self.headDict2['physdim%s' % (i-1)]
                self.headDict2['prefilter%s' % i] = self.headDict2['prefilter%s' % (i-1)]
                self.headDict2['physmin%s' % i] = self.headDict2['physmin%s' % (i-1)]
                self.headDict2['physmax%s' % i] = self.headDict2['physmax%s' % (i-1)]
                self.headDict2['digmin%s' % i] = self.headDict2['digmin%s' % (i-1)]
                self.headDict2['digmax%s' % i] = self.headDict2['digmax%s' % (i-1)]
                self.headDict2['samplescount%s' % i] = self.headDict2['samplescount%s' % (i-1)]
                self.headDict2['reserved%s' % i] = self.headDict2['reserved%s' % (i-1)]
        elif self.headDict1['signalcount'] > value:
            for i in range(value, self.headDict1['signalcount']):
                del self.channels[i]
        else:
            return
        self.headDict1['signalcount'] = value
    @property
    def reserved(self):
        return self.headDict1['reserved']