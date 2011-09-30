"""
File name: DuplicatedTransmissionItems.py
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
from WebStack.Generic import ContentType
from libPriyom import *
from API import API, CallSyntax, Argument

class DupeRecord(object):
    def __init__(self, doc, node):
        self.node = node
        self.doc = doc
        
    def add(self, broadcast, transmission):
        node = self.doc.createElementNS(XMLIntf.namespace, "duplicate-entry")
        broadcast.toDom(node)
        transmission.toDom(node)
        self.node.appendChild(node)
        

class DuplicatedTransmissionItemsAPI(API):
    title = u"getDuplicatedTransmissionItems"
    shortDescription = u"get a list of duplicated transmission items"
    
    docArgs = [
        Argument(u"stationId", u"station id", u"select the station at which to look", metavar="stationid"),
        Argument(u"classTableId", u"class table id", u"select the transmission class table to look at", metavar="classtableid"),
        Argument(u"equalFields", u"comma separated list", u"transmission item fields to look at (all if omitted)", metavar="equalfields", optional=True),
        Argument(u"includeOtherStationsWithin", u"integer seconds", u"how many seconds transmissions of other stations with same contents may be away to be selected", metavar="seconds", optional=True)
    ]
    docCallSyntax = CallSyntax(docArgs, u"?{0}&{1}&{2}&{3}")

    
    def handle(self, trans):
        stationId = self.getQueryInt("stationId", "must be a station id")
        station = self.store.get(Station, stationId)
        if station is None:
            self.parameterError("stationId", "Station does not exist")
        
        classTableId = self.getQueryInt("classTableId", "must be a class table id")
        classTable = self.store.get(TransmissionClassTable, classTableId)
        if classTable is None:
            self.parameterError("classTableId", "Class Table does not exist")
            
        matchFields = [s for s in (item.lstrip().rstrip() for item in self.query.get("equalFields", u"").split(u",")) if len(s) > 0]
        if len(matchFields) == 0:
            matchFields = None
        else:
            for field in matchFields:
                if not hasattr(classTable, field):
                    self.parameterError("equalFields", "{0} is not a valid field for this table.".format(field))
                
        includeOtherStationsWithin = self.getQueryIntDefault("includeOtherStationsWithin", 86400, "must be integer seconds")
        
        
        lastModified, items = self.priyomInterface.getDuplicateTransmissions(classTable, station, matchFields, includeOtherStationsWithin, notModifiedCheck=self.autoNotModified, head=self.head)
        trans.set_content_type(ContentType("application/xml", self.encoding))
        trans.set_header_value("Last-Modified", self.model.formatHTTPTimestamp(float(lastModified)))
        if self.head:
            return
        
        doc = self.model.getExportDoc("duplicated-transmissions")
        rootNode = doc.documentElement
        
        dupeDict = {}
        
        for bc1, tx1, txItem1, bc2, tx2, txItem2 in items:
            if tx1.ID in dupeDict:
                if tx2.ID in dupeDict:
                    continue
                rec = dupeDict[tx1.ID]
                rec.add(bc2, tx2)
                dupeDict[tx2.ID] = rec
            elif tx2.ID in dupeDict:
                rec = dupeDict[tx2.ID]
                rec.add(bc1, tx1)
                dupeDict[tx1.ID] = rec
            
            node = doc.createElementNS(XMLIntf.namespace, "duplicated-transmission")
            rec = DupeRecord(doc, node)
            rec.add(bc1, tx1)
            rec.add(bc2, tx2)
            dupeDict[tx1.ID] = rec
            dupeDict[tx2.ID] = rec
            rootNode.appendChild(node)
        
        print >>self.out, self.model.domToXml(doc, self.encoding)
