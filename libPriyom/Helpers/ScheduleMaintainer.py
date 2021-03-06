"""
File name: ScheduleMaintainer.py
This file is part of: priyomdb

LICENSE

The contents of this file are subject to the Mozilla Public License
Version 1.1 (the "License"); you may not use this file except in
compliance with the License. You may obtain a copy of the License at
http://www.mozilla.org/MPL/

Software distributed under the License is distributed on an "AS IS"
basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
License for the specific language governing rights and limitations under
the License.

Alternatively, the contents of this file may be used under the terms of
the GNU General Public license (the  "GPL License"), in which case  the
provisions of GPL License are applicable instead of those above.

FEEDBACK & QUESTIONS

For feedback and questions about priyomdb please e-mail one of the
authors:
    Jonas Wielicki <j.wielicki@sotecware.net>
"""
from storm.locals import *
from time import mktime
from datetime import datetime, timedelta

from libPriyom.Broadcast import Broadcast, BroadcastFrequency
from libPriyom.Schedule import Schedule, ScheduleLeaf
from libPriyom.Station import Station
from libPriyom.Limits import limits
import libPriyom.Helpers.TimeUtils as TimeUtils

class ScheduleMaintainerError(Exception):
    pass
        
class LeafDescriptor(object):
    def __init__(self, leaf, startOffset):
        self.leaf = leaf
        self.startOffset = startOffset
    
class LeafList(object):
    def __init__(self, store, station):
        self.items = []
        self.store = store
        self.station = station
        self.stationId = station.ID
    
    def add(self, scheduleNode, instanceStartOffset):
        i = 0
        for leaf in self.store.find(ScheduleLeaf, 
            ScheduleLeaf.StationID == self.stationId,
            ScheduleLeaf.ScheduleID == scheduleNode.ID):
            
            self.items.append(LeafDescriptor(leaf, instanceStartOffset))
            i += 1
        return i
        
class UpdateContext(object):
    def __init__(self, rootSchedule, station, store, intervalStart, intervalEnd):
        self.rootSchedule = rootSchedule
        self.station = station
        self.store = store
        self.leafList = LeafList(store, station)
        self.intervalStart = intervalStart
        self.intervalEnd = intervalEnd

class ScheduleMaintainer(object):
    def __init__(self, interface):
        self.interface = interface
        self.store = self.interface.store
        
    @staticmethod
    def incYear(dt, by):
        year = dt.year + by
        return datetime(year=year, month=1, day=1)
        
    @staticmethod
    def incMonth(dt, by):
        month = dt.month + by
        year = dt.year + int((month-1) / 12)
        month -= int((month-1) / 12) * 12
        return datetime(year=year, month=month, day=1)
        
    def getLeavesInIntervalRecurse(self, context, node, lowerConstraint, upperConstraint, allowLeaf = True):
        hasChildren = False
        for child in node.Children:
            hasChildren = True
            self.getLeavesInInterval(context, child, lowerConstraint, upperConstraint)
        if not hasChildren and allowLeaf:
            context.leafList.add(node, lowerConstraint - node.StartTimeOffset)
        
    def getLeavesInInterval_once(self, context, node, lowerConstraint, upperConstraint):
        if node.Parent is None:
            lc = max(lowerConstraint, node.StartTimeOffset)
            if node.EndTimeOffset is None:
                uc = upperConstraint
            else:
                uc = min(upperConstraint, node.EndTimeOffset)
        else:
            lc = lowerConstraint + node.StartTimeOffset
            uc = min(lowerConstraint + node.EndTimeOffset, upperConstraint)
        if (lc >= context.intervalStart):
            self.getLeavesInIntervalRecurse(context, node, lc, uc, node.Parent is not None)
            
    def getLeavesInInterval_year(self, context, node, lowerConstraint, upperConstraint):
        lcDate = datetime.fromtimestamp(lowerConstraint)
        lcDate = datetime(year=lcDate.year + node.Skip, month=1, day=1)
        ucDate = datetime(year=lcDate.year + 1, month=1, day=1)
        lc = ScheduleMaintainer.toTimestamp(lcDate)
        uc = ScheduleMaintainer.toTimestamp(ucDate)
        
        upperLimit = min(upperConstraint, context.intervalEnd)
        while (lc < upperLimit):
            if (uc > lowerConstraint):
                self.getLeavesInIntervalRecurse(context, node, lc + node.StartTimeOffset, min(lc + node.EndTimeOffset, upperConstraint, uc), lc >= context.intervalStart)
            if node.Every is None:
                break
            lcDate = ScheduleMaintainer.incYear(lcDate, node.Every)
            ucDate = ScheduleMaintainer.incYear(lcDate, 1)
            lc = ScheduleMaintainer.toTimestamp(lcDate)
            uc = ScheduleMaintainer.toTimestamp(ucDate)
            
    def getLeavesInInterval_month(self, context, node, lowerConstraint, upperConstraint):
        lcDate = datetime.fromtimestamp(lowerConstraint)
        lcDate = ScheduleMaintainer.incMonth(datetime(year=lcDate.year, month=1, day=1), node.Skip)
        ucDate = ScheduleMaintainer.incMonth(lcDate, 1)
        lc = ScheduleMaintainer.toTimestamp(lcDate)
        uc = ScheduleMaintainer.toTimestamp(ucDate)
        
        upperLimit = min(upperConstraint, context.intervalEnd)
        while (lc < upperLimit):
            if (uc > lowerConstraint):
                self.getLeavesInIntervalRecurse(context, node, lc + node.StartTimeOffset, min(lc + node.EndTimeOffset, upperConstraint, uc), lc >= context.intervalStart)
            if node.Every is None:
                break
            lcDate = ScheduleMaintainer.incMonth(lcDate, node.Every)
            ucDate = ScheduleMaintainer.incMonth(lcDate, 1)
            lc = ScheduleMaintainer.toTimestamp(lcDate)
            uc = ScheduleMaintainer.toTimestamp(ucDate)
            
    def _handleDeltaRepeat(self, context, node, lowerConstraint, upperConstraint, lcDate, interval):
        ucDate = lcDate + interval
        lc = ScheduleMaintainer.toTimestamp(lcDate)
        uc = ScheduleMaintainer.toTimestamp(ucDate)
        
        upperLimit = min(upperConstraint, context.intervalEnd)
        while (lc < upperLimit):
            if (uc > lowerConstraint):
                self.getLeavesInIntervalRecurse(context, node, lc + node.StartTimeOffset, min(lc + node.EndTimeOffset, upperConstraint, uc), lc >= context.intervalStart)
            if node.Every is None:
                break
            lcDate += interval * node.Every
            ucDate = lcDate + interval
            lc = ScheduleMaintainer.toTimestamp(lcDate)
            uc = ScheduleMaintainer.toTimestamp(ucDate)
        
    def getLeavesInInterval_week(self, context, node, lowerConstraint, upperConstraint):
        lcDate = datetime.fromtimestamp(lowerConstraint)
        lcDate = datetime(year=lcDate.year, month=lcDate.month, day=lcDate.day)
        interval = timedelta(days=7)
        
        self._handleDeltaRepeat(context, node, lowerConstraint, upperConstraint, lcDate, interval)
        
    def getLeavesInInterval_day(self, context, node, lowerConstraint, upperConstraint):
        lcDate = datetime.fromtimestamp(lowerConstraint)
        lcDate = datetime(year=lcDate.year, month=lcDate.month, day=lcDate.day)
        interval = timedelta(days=1)
        
        self._handleDeltaRepeat(context, node, lowerConstraint, upperConstraint, lcDate, interval)
        
    def getLeavesInInterval_hour(self, context, node, lowerConstraint, upperConstraint):
        lcDate = datetime.fromtimestamp(lowerConstraint)
        lcDate = datetime(year=lcDate.year, month=lcDate.month, day=lcDate.day)
        interval = timedelta(hours=1)
        
        self._handleDeltaRepeat(context, node, lowerConstraint, upperConstraint, lcDate, interval)
        
    def getLeavesInInterval(self, context, node, lowerConstraint, upperConstraint):
        method = getattr(self, "getLeavesInInterval_"+node.ScheduleKind)
        method(context, node, lowerConstraint, upperConstraint)
        
    def getLeavesInIntervalFromRoot(self, station, intervalStart, intervalEnd):
        if station.Schedule is None:
            raise ScheduleMaintainerError("Station %s has no schedule assigned" % (str(station)))
        context = UpdateContext(station.Schedule, station, self.store, intervalStart, intervalEnd)
        self.getLeavesInInterval(context, context.rootSchedule, intervalStart, intervalEnd)
        return context.leafList.items
        
    def _rebuildStationSchedule(self, station, start, end):
        for broadcast in self.store.find(Broadcast, Broadcast.StationID == station.ID, Broadcast.ScheduleLeaf != None, Broadcast.BroadcastStart > start):
            self.interface.deleteBroadcast(broadcast)
        leaves = self.getLeavesInIntervalFromRoot(station, start, end)
        for leaf in leaves:
            newBroadcast = Broadcast()
            self.store.add(newBroadcast)
            schedule = leaf.leaf.Schedule
            newBroadcast.BroadcastStart = schedule.StartTimeOffset + leaf.startOffset
            newBroadcast.BroadcastEnd = schedule.EndTimeOffset + leaf.startOffset
            newBroadcast.Type = leaf.leaf.BroadcastType
            for frequency in leaf.leaf.Frequencies:
                newFreq = BroadcastFrequency()
                self.store.add(newFreq)
                newFreq.Frequency = frequency.Frequency
                newFreq.ModulationID = frequency.ModulationID
                newBroadcast.Frequencies.add(newFreq)
            newBroadcast.Confirmed = False
            newBroadcast.Comment = None
            newBroadcast.Station = station
            newBroadcast.ScheduleLeaf = leaf.leaf
        station.ScheduleUpToDateUntil = end
        
    def updateSchedule(self, station, until, limit = None):
        now = TimeUtils.now()
        if station.Schedule is None:
            return until
        if until is None or (until - now) > limits.schedule.maxLookahead:
            until = now + limits.schedule.maxLookahead
        if station.ScheduleUpToDateUntil is None:
            start = now
        else:
            start = station.ScheduleUpToDateUntil
        if until <= start:
            return start
        if limit is not None and (until - start) > limit:
            until = start + limit
        self._rebuildStationSchedule(station, start, until)
        self.store.flush()
        return until
    
    def updateSchedules(self, until, limit = None):
        now = TimeUtils.now()
        if until is None or (until - now) > limits.schedule.maxLookahead:
            until = now + limits.schedule.maxLookahead
        validUntil = until
        if limit is None:
            limit = until
        for station in self.store.find(Station, Station.Schedule != None, Or(Station.ScheduleUpToDateUntil < until, Station.ScheduleUpToDateUntil == None)):
            start = now
            if station.ScheduleUpToDateUntil is not None:
                start = station.ScheduleUpToDateUntil
                if until <= start:
                    continue
            if (until - start) > limit:
                self._rebuildStationSchedule(station, start, start+limit)
                validUntil = min(validUntil, start+limit)
            else:
                self._rebuildStationSchedule(station, start, until)
        self.store.flush()
        return validUntil
        
