'''Datastore models.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


from google.appengine.ext import ndb


def get_user_key(user_id):
    return ndb.Key('User', int(user_id) % (1 << 48))

class Calendar(ndb.Model):
    hidden = ndb.BooleanProperty(default=False)

class EventSettings(ndb.Model):
    '''Settings for an event.'''
    pass

class Event(ndb.Model):
    starred = ndb.BooleanProperty(default=False)
    hidden = ndb.BooleanProperty(default=False)
    settings = ndb.StructuredProperty(EventSettings)

class Settings(ndb.Model):
    '''Settings for a user.'''
    pass
