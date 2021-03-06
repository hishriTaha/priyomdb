"""
File name: Station.py
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
import XMLIntf
import xml.etree.ElementTree as ElementTree
from libPriyom.PriyomBase import PriyomBase
from libPriyom.Schedule import Schedule
import libPriyom.Imports as Imports
from libPriyom.Broadcast import Broadcast
import libPriyom.Helpers.TimeUtils as TimeUtils

class Station(PriyomBase, XMLIntf.XMLStorm):
    __storm_table__ = "stations"
    ID = Int(primary = True)
    BroadcastRemoved = Int()
    EnigmaIdentifier = Unicode()
    PriyomIdentifier = Unicode()
    Nickname = Unicode()
    Description = Unicode()
    Status = Unicode()
    Location = Unicode()
    ScheduleID = Int()
    Schedule = Reference(ScheduleID, Schedule.ID)
    ScheduleConfirmed = Bool()
    ScheduleUpToDateUntil = Int(default=AutoReload)
    
    xmlMapping = {
        u"EnigmaIdentifier": "EnigmaIdentifier",
        u"PriyomIdentifier": "PriyomIdentifier",
        u"Nickname": "Nickname",
        u"Description": "Description",
        u"Status": "Status",
        u"Location": "Location"
    }
    
    def _metadataToDom(self, parentNode):
        XMLIntf.appendTextElements(parentNode,
            (
                (u"EnigmaIdentifier", self.EnigmaIdentifier),
                (u"PriyomIdentifier", self.PriyomIdentifier),
                (u"Nickname", self.Nickname)
            )
        )
        subtree = ElementTree.XML((u"<Description>"+self.Description+u"</Description>").encode("utf-8"))
        XMLIntf.applyNamespace(subtree, XMLIntf.xhtmlNamespace)
        subtree.tag = u"{{{0}}}Description".format(XMLIntf.namespace)
        parentNode.append(subtree)
        
        XMLIntf.appendTextElements(parentNode,
            [
                (u"Status", self.Status)
            ],
            noneHandler = lambda name: u""
        )
        if self.Location is not None:
            XMLIntf.appendTextElement(parentNode, u"Location", self.Location)
        if self.getIsOnAir():
            XMLIntf.SubElement(parentNode, u"on-air")
        
    def _broadcastsFromDom(self, element, context):
        for child in element:
            tag = XMLIntf.checkAndStripNamespace(element, context=context)
            if tag is None:
                continue
            if tag == u"broadcast":
                broadcast = context.importFromETree(child, Broadcast)
                if broadcast is None:
                    continue
                if broadcast.Station != self and broadcast.ScheduleLeaf is not None and broadcast.ScheduleLeaf.Station != self:
                    context.log("Cannot reassign a broadcast which is bound to a schedule leaf which is not assigned to target station.")
                else:
                    broadcast.Station = self
        
    def _transmissionsFromDom(self, element, context):
        context.log("Cannot import transmissions using station import. Please import transmissions directly or as part of broadcast imports.")
        pass
        
    def _scheduleFromDom(self, element, context):
        self.Schedule = context.importFromETree(element, Schedule)
        self.ScheduleConfirmed = element.get(u"confirmed") == "true"
        
    def loadElement(self, tag, element, context):
        try:
            {
                u"broadcasts": self._broadcastsFromDom,
                u"transmissions": self._transmissionsFromDom,
                u"schedule": self._scheduleFromDom
            }[tag](element, context)
        except KeyError:
            pass
        
    def fromDom(self, node, context):
        self.loadProperties(node, context)
        
    def getIsOnAir(self):
        return False
    
    def toDom(self, parentNode, flags = None):
        station = XMLIntf.SubElement(parentNode, u"station")
        XMLIntf.appendTextElement(station, u"ID", unicode(self.ID))
        if flags is None or not "no-metadata" in flags:
            self._metadataToDom(station)
        
        if flags is None or "schedule" in flags:
            if self.Schedule is not None:
                scheduleNode = self.Schedule.toDom(station, self.ID)
                if self.ScheduleConfirmed:
                    scheduleNode.set("confirmed", "true")
                else:
                    scheduleNode.set("confirmed", "false")
            elif self.ScheduleConfirmed:
                XMLIntf.SubElement(station, u"schedule", attrib={
                    u"confirmed": u"true"
                })
            
        if flags is None or "broadcasts" in flags:
            broadcasts = XMLIntf.SubElement(parentNode, u"broadcasts")
            for broadcast in self.Broadcasts:
                broadcast.toDom(broadcasts, flags)
        
    def __str__(self):
        return "Station: %s/%s \"%s\"" % (self.EnigmaIdentifier, self.PriyomIdentifier, self.Nickname)
        
    def broadcastRemoved(self):
        self.BroadcastRemoved = int(TimeUtils.now())
        
    def __unicode__(self):
        return u"{1}{2}{0}".format(
            u" (" + self.Nickname + u")" if len(self.Nickname) > 0 else u"",
            self.EnigmaIdentifier + (u" / " if len(self.EnigmaIdentifier) > 0 and len(self.PriyomIdentifier) > 0 else u""),
            self.PriyomIdentifier
        )
