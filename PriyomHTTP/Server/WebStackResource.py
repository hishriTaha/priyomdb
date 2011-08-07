from WebStack.Resources.ResourceMap import MapResource
from WebStack.Resources.LoginRedirect import LoginRedirectResource, LoginRedirectAuthenticator
from WebStack.Resources.Login import LoginResource, LoginAuthenticator
from WebStack.Resources.Selectors import EncodingSelector, PathSelector

from APIDatabase import APICapability
from Authentication import AuthenticationSelector
from Authorization import AuthorizationSelector
from WebModel import WebModel
from Documentation import DocumentationSelector
import libPriyom
from Resources import *
from Resources.API import *
#from Resources.API.FindStations import FindStations
#from Resources.API.FindBroadcasts import FindBroadcasts
#from Resources.API.FindTransmissions import FindTransmissions
#from Resources.API.UpcomingBroadcasts import UpcomingBroadcasts

def get_site_map(priyomInterface):
    model = WebModel(priyomInterface)
    
    apiMap = MapResource({
        "getUpcomingBroadcasts": UpcomingBroadcastsAPI(model),
        "import": AuthorizationSelector(ImportAPI(model), "transaction"),
        "listStations": AuthorizationSelector(ListAPI(model, libPriyom.Station), "list"),
        "listBroadcasts": AuthorizationSelector(ListAPI(model, libPriyom.Broadcast), "list"),
        "listTransmissionClasses": AuthorizationSelector(ListAPI(model, libPriyom.TransmissionClass), "list"),
        "listTransmissions": AuthorizationSelector(ListAPI(model, libPriyom.Transmission), "list"),
        "getSession": SessionAPI(model)
    })
    
    return EncodingSelector(AuthenticationSelector(model.store,
        MapResource({
            "station": StationResource(model),
            "broadcast": IDResource(model, libPriyom.Broadcast),
            "transmission": IDResource(model, libPriyom.Transmission),
            "schedule": IDResource(model, libPriyom.Schedule),
            "call": apiMap,
            "doc": DocumentationSelector(apiMap),
            "": EmptyResource(model)
        })),
        "utf-8"
    )
