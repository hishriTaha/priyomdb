from WebStack.Generic import ContentType
from libPriyom import *
from API import API, CallSyntax, Argument
from ...limits import queryLimits
import time
from datetime import datetime, timedelta
from libPriyom.Formatting import priyomdate

class InstanciateSchedulesAPI(API):
    title = u"instanciateSchedules"
    shortDescription = u"instanciate schedules"
    
    docArgs = [
        Argument(u"stationId", u"station ID", u"Restrict the instanciation to a single station", metavar="stationid", optional=True),
    ]
    docCallSyntax = CallSyntax(docArgs, u"?{0}")
    docRequiredPrivilegues = u"instanciate"
    
    def __init__(self, model):
        super(InstanciateSchedulesAPI, self).__init__(model)
        self.allowedMethods = frozenset(("POST", "GET", "HEAD"))
    
    def handle(self, trans):
        stationId = self.getQueryIntDefault("stationId", None, "must be integer")
        
        trans.set_content_type(ContentType("text/plain", self.encoding))
        if self.head:
            return
        if trans.get_request_method() == "GET":
            print >>self.out, u"failed: Call this resource with POST to perform instanciation.".encode(self.encoding)
            return
        
        generatedUntil = 0
        if stationId is None:
            generatedUntil = self.priyomInterface.scheduleMaintainer.updateSchedules(None)
        else:
            generatedUntil = self.priyomInterface.scheduleMaintainer.updateSchedule(self.store.get(Station, stationId), None)
        
        print >>self.out, u"success: valid until {0}".format(datetime.fromtimestamp(generatedUntil).strftime(priyomdate)).encode(self.encoding)
