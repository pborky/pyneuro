
import re
import datetime

## Used for the regex construction

HEAD =     [r'(?P<version>[\x20-\x7e]{8})',
            r'(?P<patient>[\x20-\x7e]{80})',
            r'(?P<recording>[\x20-\x7e]{80})',
            r'(?P<startDate>[\x20-\x7e]{8})',
            r'(?P<startTime>[\x20-\x7e]{8})',
            r'(?P<headBytes>[\x20-\x7e]{8})',
            r'(?P<reserved>[\x20-\x7e]{44})',
            r'(?P<recordCount>[\x20-\x7e]{8})',
            r'(?P<recordDuration>[\x20-\x7e]{8})',
            r'(?P<channelCount>[0-9\x20]{4})',
            r'(?P<channels>[\x20-\x7e]+)' ]


CHANNELS = [r'(?P<label%s>[\x20-\x7e]{16})',
            r'(?P<transducer%s>[\x20-\x7e]{80})',
            r'(?P<physDim%s>[\x20-\x7e]{8})',
            r'(?P<physMin%s>[\x20-\x7e]{8})',
            r'(?P<physMax%s>[\x20-\x7e]{8})',
            r'(?P<digMin%s>[\x20-\x7e]{8})',
            r'(?P<digMax%s>[\x20-\x7e]{8})',
            r'(?P<prefilter%s>[\x20-\x7e]{80})',
            r'(?P<samplesCount%s>[\x20-\x7e]{8})',
            r'(?P<reserved%s>[\x20-\x7e]{32})' ]

PATIENT = r'(?P<id>\w+)\s+(?P<sex>F|M)\s+(?P<day>[0-9]{2})-(?P<month>[a-zA-Z]{3})-(?P<year>[0-9]{4})\s+(?P<name>.+)'

RECORDING = r'Startdate\s+(?P<day>[0-9]{2})-(?P<month>[a-zA-Z]{3})-(?P<year>[0-9]{4})\s+(?P<id>\w+)\s+(?P<investigator>\w+)\s+(?P<equipment>\w+)(?:\s+(?P<other>\w+))?'

MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

HEAD_SIZE = 256
CHANEL_SIZE = 256

class HeaderBase(object):
    def __setattr__(self, name, value):
        if name in [ '__dict__', '_data' ] or '_data' not in self.__dict__:
            object.__setattr__(self, name, value)
        _data = self.__dict__['_data']
        if name in _data and isinstance(_data, dict):
            _data[name] = value
        else:
            object.__setattr__(self, name, value)
    
    def __getattribute__(self, name):
        if name in [ '__dict__', '_data' ] or '_data' not in self.__dict__:
            return object.__getattribute__(self, name)
        _data = self.__dict__['_data']
        if name in _data and isinstance(_data, dict):
            return _data[name]
        else:
            return object.__getattribute__(self, name)

class Header(HeaderBase):
    def copy(self):
        head = Header()
        head._data = self._data.copy()
        if isinstance(head.patient._data, str):
            head.patient = HeaderPatient(self.patient._data, head)
        else:
            head.patient = HeaderPatient(self.patient._data.copy(), head)
        if isinstance(head.recording._data, str):
            head.recording = HeaderRecording(self.recording._data, head)
        else:
            head.recording = HeaderRecording(self.recording._data.copy(), head)
        head.channels = []
        for i in range(head.channelCount):
            head.channels.append(HeaderChannel(self.channels[i]._data.copy(), head))
        return head
    
    def __init__(self, head = None):
        if head is None:
            self._data = {}
            
            self._data['version'] = None
            self._data['reserved'] = None
            
            self._data['startDate'] = None
            self._data['startTime'] = None
            self._data['startDateTime'] = None
            
            self._data['headBytes'] = None
            self._data['recordCount'] = None
            self._data['recordDuration'] = None
            self._data['channelCount'] = 0
            
            self._data['channels'] = []
            
            p = {'birthDate': None,
                 'id': None,
                 'name': None,
                 'sex':  None}
            self._data['patient'] = HeaderPatient(p, self)
            
            p = {'equipment': None,
                 'id': None,
                 'investigator': None,
                 'other': None,
                 'startDate': None }
            self._data['recording'] = HeaderRecording(p, self)
        elif isinstance(head,str):
            m = re.match(r''.join(HEAD), head)
            if m is None:
                raise ValueError('Not a valid EDF header.')
            self._data = m.groupdict()
            self._data['version'] = self._data['version'].strip()
            self._data['patient'] = self._data['patient'].strip()
            
            self._data['startDate'] = self._data['startDate'].strip()
            self._data['startTime'] = self._data['startTime'].strip()
            
            self._data['headBytes'] = int(self._data['headBytes'])
            self._data['recordCount'] = int(self._data['recordCount'])
            self._data['recordDuration'] = int(self._data['recordDuration'])
            self._data['channelCount'] = int(self._data['channelCount'])
            
            try:
                dt = [ int(s) for s in self._data['startDate'].split('.') ]
                tm = [ int(s) for s in self._data['startTime'].split('.') ]
                
                dt.reverse()
                
                if dt[0] < 85:
                    dt[0] += 2000
                else:
                    dt[0] += 1900
                self._data['startDateTime'] = datetime.datetime(*(dt+tm))
            except:
                self._data['startDateTime'] = None
            
            m = re.match(PATIENT, self._data['patient'])
            if m is not None:
                p = m.groupdict()
                y = int(p['year'])
                m = MONTHS.index(p['month'])+1
                d = int(p['day'])
                del p['year'], p['month'], p['day']
                p['birthDate'] = datetime.date(y, m, d)
                self._data['patient'] = HeaderPatient(p, self)
            
            m = re.match(RECORDING, self._data['recording'])
            if m is not None:
                p = m.groupdict()
                y = int(p['year'])
                m = MONTHS.index(p['month'])+1
                d = int(p['day'])
                del p['year'], p['month'], p['day']
                p['startDate'] = datetime.date(y, m, d)
                if self._data['startDateTime'] is None:
                    tm = [ int(s) for s in self._data['startTime'].split('.') ]
                    self._data['startDateTime'] = datetime.datetime(y,m,d,*tm)
                self._data['recording'] = HeaderRecording(p, self)
            
            channels = self._data['channels']
            del self._data['channels']
            r = []
            for s in CHANNELS:
                for i in range(self._data['channelCount']):
                    r.append(s % i)
            m = re.match(r''.join(r), channels)
            
            if m is None:
                raise ValueError('Not a valid EDF header.')
                
            channels = m.groupdict()
            channels2 = []
            
            for i in range(self._data['channelCount']):
                channels2.append({})
                
                channels2[i]['label'] = channels['label%s' % i].strip()
                channels2[i]['transducer'] = channels['transducer%s' % i].strip()
                channels2[i]['physDim'] = channels['physDim%s' % i].strip()
                channels2[i]['prefilter'] = channels['prefilter%s' % i].strip()
                
                channels2[i]['physMin'] = int(channels['physMin%s' % i])
                channels2[i]['physMax'] = int(channels['physMax%s' % i])
                channels2[i]['digMin'] = int(channels['digMin%s' % i])
                channels2[i]['digMax'] = int(channels['digMax%s' % i])
                channels2[i]['samplesCount'] = int(channels['samplesCount%s' % i])
            
            self._data['channels'] = [ HeaderChannel(channels2[i], self) for i in range(self._data['channelCount']) ] 
        else:
            raise ValueError('String is required.')
    
    @property
    def text(self):
        y = self.startDateTime.year % 100
        m = self.startDateTime.month
        d = self.startDateTime.day
        h = self.startDateTime.hour
        mi = self.startDateTime.minute
        s = self.startDateTime.second
        
        chan = []
        for i in range(10):
            chan.append([])
        for i in range(self.channelCount):
            c = self.channels[i]
            chan[0].append('{0:<16}'.format(c.label))
            chan[1].append('{0:<80}'.format(c.transducer))
            chan[2].append('{0:<8}'.format(c.physDim))
            chan[3].append('{0:<8}'.format(c.physMin))
            chan[4].append('{0:<8}'.format(c.physMax))
            chan[5].append('{0:<8}'.format(c.digMin))
            chan[6].append('{0:<8}'.format(c.digMax))
            chan[7].append('{0:<80}'.format(c.prefilter))
            chan[8].append('{0:<8}'.format(c.samplesCount))
            chan[9].append('{0:<32}'.format(''))
        for i in range(10):
            chan[i] = ''.join(chan[i])
        chan = ''.join(chan)
        
        return '{0:<8}{1:<80}{2:<80}{3:0>2}.{4:0>2}.{13:0>2}{5:0>2}.{6:0>2}.{7:0>2}{8:<8}{9:<44}{10:<8}{11:<8}{12:<4}{14}'.format(
                self.version, 
                self.patient.text, 
                self.recording.text, 
                d,m,h,mi,s,
                self.headBytes,
                self.reserved,
                self.recordCount,
                self.recordDuration,
                self.channelCount,
                y, chan
            )
    
    def __setattr__(self, name, value):
        HeaderBase.__setattr__(self, name, value)
        if name == 'channelCount':
            if len(self.channels) > value:
                for i in (value, len(self.channels)):
                    del self.channels[i]
            elif len(self.channels) < value:
                if len(self.channels) > 0:
                    channel = self.channels[0]._data.copy()
                else:
                    channel = {'label': None,
                                'transducer': None,
                                'physDim':None,
                                'prefilter': None,
                                'reserved': None,
                                'physMin': None,
                                'physMax': None,
                                'digMin': None,
                                'digMax': None,
                                'samplesCount': None}
                while len(self.channels) < value:
                    self.channels.append(HeaderChannel(channel.copy(), self))
            
            self.headerSize = HEAD_SIZE + value * CHANEL_SIZE
    
class HeaderRecording(HeaderBase):
    def __init__(self, data, header):
        self._data = data
        self._header = header
    @property
    def isPlain(self):
        return isinstance(self._data,str)
    @property
    def plain(self):
        if self.isPlain:
            return self._data
        else:
            return str(self._data)
    @plain.setter
    def plain(self, value):
        self._data = value
    @property
    def text(self):
        if self.isPlain:
            return self.plain
        else:
            data = [self.startDate.day, 
                    MONTHS[self.startDate.month-1], 
                    self.startDate.year, 
                    self.id, 
                    self.investigator, 
                    self.equipment, 
                    self.other ]
            if self.other is None:
                return 'Startdate {0:0>2}-{1}-{2:0>4} {3} {4} {5}'.format(*data)
            else:
                return 'Startdate {0:0>2}-{1}-{2:0>4} {3} {4} {5} {6}'.format(*data)
class HeaderPatient(HeaderBase):
    def __init__(self, data, header):
        self._data = data
        self._header = header
    @property
    def isPlain(self):
        return isinstance(self._data,str)
    @property
    def plain(self):
        if self.isPlain:
            return self._data
        else:
            return str(self._data)
    @plain.setter
    def plain(self, value):
        self._data = value
    @property
    def text(self):
        if self.isPlain:
            return self.plain
        else:
            data = [self.id, 
                    self.sex, 
                    self.birthDate.day, 
                    MONTHS[self.birthDate.month-1], 
                    self.birthDate.year, 
                    self.name]
            return '{0} {1} {2:0>2}-{3}-{4:0>4} {5}'.format(*data)
    
class HeaderChannel(HeaderBase):
    def __init__(self, data, header):
        self._data = data
        self._header = header
    @property
    def samplingFrequency(self):
        return float(self.samplesCount) / float(self._header.recordDuration)
    @samplingFrequency.setter
    def samplingFrequency(self, value):
        self.samplesCount = value * self._header.recordDuration
    @property
    def isPlain(self):
        return isinstance(self._data,str)
    @property
    def plain(self):
        if isinstance(self._data,str):
            return self._data
        else:
            return str(self._data)
    @plain.setter
    def plain(self, value):
        self._data = value

## Deafault header
HEADER = Header()
HEADER.version = '0'
HEADER.patient.plain = 'TRIGGERING USER'
HEADER.recording.plain = 'TRIGGERING'
HEADER.startDateTime =  datetime.datetime.now()
HEADER.headBytes = 512
HEADER.reserved = 'BIOSEMI'
HEADER.recordCount = -1
HEADER.recordDuration = 1
HEADER.channelCount = 1
HEADER.channels[0].label = 'DUMMY'
HEADER.channels[0].transducer = 'UNIVERSAL'
HEADER.channels[0].physDim = 'mV'
HEADER.channels[0].prefilter = 'No prefiltering, raw data'
HEADER.channels[0].physMin = 0
HEADER.channels[0].physMax = 255
HEADER.channels[0].digMin = 0
HEADER.channels[0].digMax = 255
HEADER.channels[0].samplesCount = 256

