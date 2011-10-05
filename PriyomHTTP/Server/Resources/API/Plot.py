"""
File name: Plot.py
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
from ...APIDatabase import APIFileResource
import mmap

class PlotAPI(API):
    def __init__(self, model, dataSource, renderer, queryArgs, resourceType, cls, idOrKey, fileFormat=u"{0}/plots/{1}.png", contentType=ContentType("image/png"), allowNoId=False, **kwargs):
        super(API, self).__init__(model)
        self.dataSource = dataSource
        self.renderer = renderer
        self.plotArgs = kwargs
        self.allowedMethods = frozenset(['GET'])
        self.queryArgs = queryArgs
        self.idOrKey = idOrKey
        self.cls = cls
        self.resourceType = resourceType
        cls.Modified
        self.allowNoId = allowNoId
        self.fileFormat = fileFormat
        self.contentType = contentType
        
    def plot(self, resource):
        tmpArgs = self.plotArgs.copy()
        tmpArgs.update(self.args)
        self.renderer.plotGraph(self.dataSource, resource.FileName, dpi=72, format="png", transparent=True, **args)
        
    def handle(self, trans):
        args = {}
        for queryName, typecast, kwName in self.queryArgs:
            try:
                args[kwName] = self.query[queryName] if typecast is None else typecast(self.query[queryName])
            except TypeError as e:
                self.parameterError(queryName, unicode(e))
            except ValueError as e:
                self.parameterError(queryName, unicode(e))
        if type(idOrKey) == int:
            id = idOrKey
        else:
            id = int(args.get(idOrKey, 0))
        if id == 0:
            if not self.allowNoId:
                self.parameterError(u"", u"No id specified")
            lastModified = self.store.find(cls).max(cls.Modified)
        else:
            obj = self.store.get(cls, id)
            if obj is None:
                self.parameterError(u"", u"Could not find {0} with id {1}.".format(unicode(cls), id)
            lastModified = obj.Modified
        
        trans.set_content_type(self.contentType)
        trans.set_header_value("Last-Modified", self.model.formatHTTPTimestamp(lastModified))
        self.autoNotModified(lastModified)
        
        self.args = args
        item = APIFileResource.createOrFind(cls.__storm_table__, id, resourceType, lastModified, self.fileFormat, self.plot)
        if item is not None:
            img = open(item.FileName, "rb")
            map = mmap.mmap(img, 0, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ)
            print >>self.out, map.read(map.size())
            map.close()
            img.close()
        else:
            raise Exception(u"Could not create resource.")
        
