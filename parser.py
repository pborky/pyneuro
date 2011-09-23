
import re

class Header:
    def __init__(self, header):
        self.header = header
    def text(self):
        return self.header

class Container:
    def append(self, matcher):
        raise Exception('Not implemented.')

class Action:
    def __init__(self, client, matcher):
        self.client = client
        self.matcher = matcher
    def execute(self):
        raise Exception('Not implemented.')

class MessageAction(Action):
    pass

class ResultMessageAction(MessageAction):
    def __init__(self, client, valid):
        MessageAction.__init__(self, client, None)
        self.valid = valid

RESULT_OK = ResultMessageAction(None, True)
RESULT_NOK = ResultMessageAction(None, False)

class SampleMessageAction(MessageAction,Container):
    def __init__(self, client, matcher):
        MessageAction.__init__(self, client, matcher)
        self.nSamples,samples = self.convert(matcher)
        self.samples = []
        self.samples.append(samples)
    def execute(self):
        watchers = self.caller.getWatchers(self.client.id)
        self.caller.message(self.client.id, RESULT_OK)
        for watcher in watchers:
            self.caller.message(watcher, self)
    def text(self):
        fmt = '! {0} {2} {1} '+' '.join(['{'+str(i+3)+'}' for i in range(self.nSamples) ])
        return fmt.format(self.client.id, self.nSamples, *self.samples)
    def convert(self, matcher):
        nSamples = int(self.matcher.group(2))
        samples = [ int(self.matcher.group(1)) ]
        for i in self.matcher.group(3).split():
            samples.append(float(i))
        if len(samples)-1 != nSamples:
            raise ValueError('Inconsistent packet count.')
        return (nSamples, tuple(samples))
    def append(self, matcher):
        nSamples,samples = self.convert(matcher)
        if nSamples != self.nSamples:
            raise ValueError("Wrong value")
        self.samples.append(samples)

class RoleMessageAction(MessageAction):
    def __init__(self, client, role):
        MessageAction.__init__(self, client, None)
        self.role = role
    def text(self):
        return str(self.role)
        
class HeaderMessageAction(MessageAction):
    def __init__(self, client, header):
        MessageAction.__init__(self, client, None)
        self.header = Header(header)
    def text(self):
        return self.header.text()

class StatusMessageAction(MessageAction):
    def __init__(self, client, clients):
        MessageAction.__init__(self, client, None)
        self.clients = clients
    def text(self):
        nClients = len(self.clients)
        retarr = [ '{0} clients connected'.format(nClients) ]
        for key,val in self.clients.items():
            retarr.append('{0}:{1}'.format(key, val.getRole()))
        return '\r\n'.join(retarr)

class CommandAction(Action):
    pass

class ResultCommandAction(CommandAction):
    def __init__(self, client, status):
        CommandAction.__init__(self, client, False)
        self.status = status
    def execute(self):
        self.caller.message(self.client.id, self.status)

class StatusCommandAction(CommandAction):
    def execute(self):
        clients = self.caller.getClients()
        status = StatusMessageAction(self.client, clients)
        self.caller.message(self.client.id, [RESULT_OK, status])

class GetheaderCommandAction(CommandAction):
    def __init__(self, client, matcher):
        CommandAction.__init__(self, client, matcher)
        self.id = int(self.matcher.group(1))
    def execute(self):
        header = HeaderMessageAction(self.client, client.getHeader(self.id))
        self.caller.message(self.client.id, [ RESULT_OK, header ])

class SetheaderCommandAction(CommandAction):
    def __init__(self, client, matcher):
        CommandAction.__init__(self, client, matcher)
        self.header = Header(self.matcher.group(1))
    def execute(self):
        self.client.setHeader(self.header)
        self.caller.message(self.client.id, RESULT_OK)

class EEGCommandAction(CommandAction):
    def execute(self):
        self.client.setRole('EEG') 
        self.caller.message(self.client.id, RESULT_OK)

class DisplayCommandAction(CommandAction):
    def execute(self):
        self.client.setRole('Display')
        self.caller.message(self.client.id, RESULT_OK)

class RoleCommandAction(CommandAction):
    def execute(self):
        role = RoleMessageAction(self.client, self.client.getRole())
        self.caller.message(self.client.id, [ RESULT_OK, role ])

class WatchCommandAction(CommandAction):
    def __init__(self, client, matcher):
        CommandAction.__init__(self, client, matcher)
        self.id = int(self.matcher.group(1))
    def execute(self):
        try:
            if self.caller.getRole(self.id) != 'EEG':
                raise Exception('Role "EEG" is required.')
            self.client.setWatch(self.id)
            self.caller.message(self.client.id, RESULT_OK)
        except:
            self.caller.message(self.client.id, RESULT_NOK)
            raise

class UnwatchCommandAction(CommandAction):
    def __init__(self, client, matcher):
        CommandAction.__init__(self, client, matcher)
        self.id = int(self.matcher.group(1))
    def execute(self):
        try:
            if self.caller.getRole(self.id) != 'EEG':
                raise Exception('Role "EEG" is required.')
            self.client.setUnwatch(self.id) 
            self.caller.message(self.client.id, RESULT_OK)
        except:
            self.caller.message(self.client.id, RESULT_NOK)
            raise

class WatchallCommandAction(CommandAction):
    def execute(self):
        try:
            if self.caller.getRole(self.id) != 'EEG':
                raise Exception('Role "EEG" is required.')
            self.client.setWatch() 
            self.caller.message(self.client.id, RESULT_OK)
        except:
            self.caller.message(self.client.id, RESULT_NOK)
            raise

class UnwatchallCommandAction(CommandAction):
    def execute(self):
        try:
            if self.caller.getRole(self.id) != 'EEG':
                raise Exception('Role "EEG" is required.')
            self.client.setUnwatch()
            self.caller.message(self.client.id, RESULT_OK)
        except:
            self.caller.message(self.client.id, RESULT_NOK)
            raise
    
map = [
       (re.compile(r'^!\s+([0-9]+)\s+([0-9]+)\s+(.*)$'), SampleMessageAction),
       (re.compile(r'^status$'), StatusCommandAction),
       (re.compile(r'^getheader\s+([0-9]+)$'), GetheaderCommandAction),
       (re.compile(r'^setheader\s(.+)$'), SetheaderCommandAction),
       (re.compile(r'^eeg$'), EEGCommandAction),
       (re.compile(r'^display$'), DisplayCommandAction),
       (re.compile(r'^role$'), RoleCommandAction),
       (re.compile(r'^watch\s([0-9]+)$'), WatchCommandAction),
       (re.compile(r'^unwatch\s([0-9]+)$'), UnwatchCommandAction),
       (re.compile(r'^watch\s+$'), WatchallCommandAction),
       (re.compile(r'^unwatch\s+$'), UnwatchallCommandAction)       
]

class Parser(object):
    def __init__(self, caller):
        self.caller = caller
    def parse(msg, client = None, container = None):
        for pattern, Class in map:
            matcher = pattern.match(msg)
            if matcher is not None:
                if container is not None and isinstance(container, Container):
                    container.append(matcher)
                    return container
                else:
                    if client is None:
                        raise ValueError('One of the "client" or "container" is supposed to be present.')
                    return Class(client, matcher)
        return ResultCommandAction(client, RESULT_NOK)
