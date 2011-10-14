class WrapFunction(object):
    def __init__(self, func, description):
        self.func = func
        self.description = description
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    
    def __str__(self):
        return str(self.description)
        
    def __unicode__(self):
        return self.description

class Typecasts(object):
    __init__ = None
    
    int = WrapFunction(int, u"integer number")
    long = WrapFunction(long, u"integer number")
    float = WrapFunction(float, u"decimal number")
    unicode = WrapFunction(unicode, u"character string")
    str = WrapFunction(str, u"character string")
    
    @staticmethod
    def Bool():
        def tchelper(s):
            if type(s) in [int, float, long]:
                return bool(s)
            else:
                s = unicode(s).lower()
                return (s == u"true" or s == u"yes")
        return WrapFunction(tchelper, u""""true" or "false\"""")
    
    @staticmethod
    def RangeCheck(typecast, min, max):
        def tchelper(s):
            numeric = typecast(s)
            if numeric is None:
                return None
            if ((min is not None) and (min > numeric)) or ((max is not None) and (max < numeric)):
                raise ValueError(u"value out of bounds ({1}..{2}): {0}".format(i, min if min is not None else u"-infinity", max if max is not None else u"infinity"))
            return numeric
        return WrapFunction(tchelper, u"{0} within a range of ({1}..{2})".format(unicode(typecast), min, max))
    
    @staticmethod
    def validStormObject(type, store):
        def valid_storm_object(id):
            obj = store.get(type, int(id))
            if obj is None:
                raise ValueError(u"{0} does not identify a valid {1}".format(id, type))
            return obj
        return valid_storm_object
        
    @staticmethod
    def validStation(store):
        def valid_station(id):
            intId = None
            try:
                intId = int(id)
            except ValueError:
                pass
            if intId is not None:
                obj = store.get(Station, intId)
                if obj is not None:
                    return obj
            obj = store.find(Station, Station.EnigmaIdentifier == unicode(id)).any()
            if obj is not None:
                return obj
            obj = store.find(Station, Station.PriyomIdentifier == unicode(id)).any()
            if obj is None:
                raise ValueError(u"{0} does not identify a valid {1}".format(id, Station))
            return obj
        return WrapFunction(valid_station, u"valid station identifier (a db id identifying a station, enigma identifier or priyom identifier)")
        
    @staticmethod
    def PriyomTimestamp(allowNone=False, asDate=True):
        def priyom_timestamp(s):
            if allowNone and (type(s) == str or type(s) == unicode):
                if s.lower() == "none":
                    return None
            if asDate:
                return datetime.strptime(s, Formatting.priyomdate)
            else:
                return TimeUtils.toTimestamp(datetime.strptime(s, Formatting.priyomdate))
        return WrapFunction(priyom_timestamp, u"datetime according to the standard priyom date format (YYYY-MM-DDTHH:MM:SS)")
    
    @staticmethod
    def AllowBoth(type1, type2):
        def redefine_both_callable(s):
            try:
                return type1(s)
            except Exception as e1:
                try:
                    return type2(s)
                except Exception as e2:
                    raise ValueError(u"{1} and {2}".format(repr(s), e1, e2))
        return WrapFunction(redefine_both_callable, u"{0} or {1}".format(unicode(type1), unicode(type2)))
        
    @staticmethod
    def EmptyString():
        def empty(s):
            origs = s
            if type(s) != str and type(s) != unicode:
                s = unicode(s)
            if len(s.lstrip().rstrip()) > 0:
                raise ValueError(u"{0} is not empty".format(repr(origs)))
            return u""
        return WrapFunction(empty, u"empty")
