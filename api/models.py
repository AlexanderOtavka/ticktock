'''Endpoints models.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


from google.appengine.ext import ndb
from endpoints_proto_datastore.ndb import EndpointsModel


class Calendar(EndpointsModel):
    name = ndb.StringProperty()
    hidden = ndb.BooleanProperty(default=False)
    color = ndb.StringProperty()
    link = ndb.StringProperty()

class EventSettings(EndpointsModel):
    '''Settings for an event.'''
    pass

class Event(EndpointsModel):
    name = ndb.StringProperty()
    start_date = ndb.DateTimeProperty()
    end_date = ndb.DateTimeProperty()
    starred = ndb.BooleanProperty(default=False)
    link = ndb.StringProperty()
    settings = ndb.StructuredProperty(EventSettings)

class Settings(EndpointsModel):
    '''Settings for a user.'''
    pass
