# encoding=utf-8
from storm.locals import *
from storm.exceptions import NoStoreError
import time
from datetime import datetime

def now():
    return int(time.mktime(datetime.utcnow().timetuple()))

def AutoSetModified(instance, propertyName, newValue):
    instance.Modified = now()
    return newValue

class PriyomBase(object):
    Created = Int()
    Modified = Int()
    _knownModified = None
    
    def __init__(self):
        self.Created = now()
        self.Modified = now()
    
    def _forceStore(self, exceptionMessage = None):
        store = Store.of(self)
        if store is None:
            raise NoStoreError(exceptionMessage if exceptionMessage is not None else u"A store is needed to do that.")
        return store
    
    def invalidated(self):
        self._forceStore(u"A store is needed to determine the valid status of an object.")
        self.Modified = AutoReload
        if self._knownModified is None:
            self._knownModified = self.Modified
            return True
        if self._knownModified != self.Modified:
            return False
        
    def validate(self):
        store = self._forceStore(u"A store is needed to validate an object.")
        self.Modified = AutoReload
        if self._knownModified != self.Modified:
            store.autoreload(self)
            self._knownModified = self.Modified