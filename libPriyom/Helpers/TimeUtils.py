"""
File name: TimeUtils.py
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
from datetime import datetime, timedelta
from calendar import timegm

monthname = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def toTimestamp(datetime):
    return timegm(datetime.utctimetuple())
    
def toDatetime(timestamp):
    return datetime.utcfromtimestamp(timestamp)
    
def nowDate():
    return datetime.utcnow()
    
def now():
    return toTimestamp(nowDate())

def nextMonth(dt):
    if dt.month == 12:
        return datetime(year=dt.year+1, month=1, day=1)
    else:
        return datetime(year=dt.year, month=dt.month+1, day=1)

def monthTimeRange(year, month):
    first = datetime(year, month, 1)
    return (toTimestamp(first), toTimestamp(nextMonth(first)))

def yearTimeRange(year):
    return (toTimestamp(datetime(year, 1, 1)), toTimestamp(datetime(year+1, 1, 1)))

def calendarTimeRange(year, month=None):
    if month is not None:
        return monthTimeRange(year, month)
    else:
        return yearTimeRange(year)

fromTimestamp = toDatetime
