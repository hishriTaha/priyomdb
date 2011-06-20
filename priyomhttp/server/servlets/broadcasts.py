from ..limits import queryLimits
from storm.locals import *
import baseServlet
from baseServlet import ServletError, ServletInvalidQueryError
import libpriyom.interface
from libpriyom.stations import Station
from libpriyom.broadcasts import Broadcast
import libpriyom.helpers.selectors
from ..servlets import register
import time, datetime

class BroadcastsServlet(baseServlet.Servlet):
    def _now(self):
        return int(time.mktime(datetime.datetime.utcnow().timetuple()))
        
    def _writeList(self, broadcasts, wfile):
        doc = self.priyomInterface.createDocument("priyom-broadcasts-export")
        rootNode = doc.documentElement
        for broadcast in broadcasts:
            broadcast.toDom(rootNode, frozenset())
        self.setHeader("Content-Type", "text/xml; charset=utf-8")
        wfile.write(doc.toprettyxml().encode("utf-8"))
    
    def doUpcoming(self, pathSegments, arguments, wfile):
        if len(pathSegments) != 1:
            raise ServletInvalidQueryError("Invalid argument count")
        update = not ("no-update" in arguments)
        all = "all" in arguments
        
        try:
            stationId = int(arguments["station"])
        except KeyError:
            stationId = None
        except ValueError:
            raise ServletInvalidQueryError("Non-integer station id")
            
        maxTimeRange = queryLimits.broadcasts.maxTimeRangeForUpdatingQueries if stationId is None else queryLimits.broadcasts.maxTimeRangeForStationBoundUpdatingQueries
        
        if pathSegments[0] == "":
            timeLimit = maxTimeRange # automatically set
        else:
            try:
                timeLimit = int(pathSegments[0])
            except ValueError:
                raise ServletInvalidQueryError("Non-integer time range (expected in unit of seconds)")
            #if update and (timeLimit > maxTimeRange):
            #    raise ServletInvalidQueryError("Time range exceeds maximum for updating queries (%d). You may want to try the \"no-update\" flag, but you may receive outdated information" % maxTimeRange)
        
            
        now = self._now()
        if update:
            untilDate = datetime.datetime.fromtimestamp(now)
            untilDate += datetime.timedelta(seconds=timeLimit)
            untilDate = datetime.datetime(year=untilDate.year, month=untilDate.month, day=untilDate.day)
            until = int(time.mktime(untilDate.timetuple()))
            if stationId is None:
                validUntil = self.priyomInterface.scheduleMaintainer.updateSchedules(until, maxTimeRange)
            else:
                station = self.store.get(Station, stationId)
                if station is None:
                    raise ServletError(404, "Station does not exist (no update query possible)")
                validUntil = self.priyomInterface.scheduleMaintainer.updateSchedule(station, until, maxTimeRange)
            if validUntil < until:
                self.setReplyCode(200, "Information may be out of date")
            self.setHeader("Expires", self.formatTimestamp(validUntil))
        
        where = And(Or(Broadcast.BroadcastEnd > now, Broadcast.BroadcastEnd == None), (Broadcast.BroadcastStart < (now + timeLimit)))
        if not all:
            where = And(where, Broadcast.Type == u"data")
        if stationId is not None:
            where = And(where, Broadcast.StationID == stationId)
        
        resultSet = self.store.find(Broadcast, where)
        self._limitResults(resultSet, arguments)
        broadcasts = [broadcast for broadcast in resultSet]
        if len(broadcasts) == 0:
            raise ServletError(404, "No upcoming %sbroadcasts within the next %d seconds" % ("" if all else "data (you may want to try the \"all\" flag) ", timeLimit))
        
        self._writeList(broadcasts, wfile)
    
    def do_GET(self, pathSegments, arguments, rfile, wfile):
        try:
            method = {
                "upcoming": self.doUpcoming
            }[pathSegments[0]]
        except KeyError:
            raise ServletInvalidQueryError("Unknown selector")
        method(pathSegments[1:], arguments, wfile)

register("broadcasts", BroadcastsServlet, True, "broadcasts.py")
