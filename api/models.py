"""Datastore models."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

from google.appengine.ext import ndb


def get_user_key(user_id):
    """
    Get an ndb key for a user based on a user id.

    :type user_id: unicode
    :rtype: ndb.Key
    """
    return ndb.Key("User", int(user_id) % (1 << 48))


class Calendar(ndb.Model):
    """
    Data model for all calendar properties stored in the datastore.

    :type hidden: bool
    """
    hidden = ndb.BooleanProperty(default=False)


class EventSettings(ndb.Model):
    """Settings for an event."""
    pass


class Event(ndb.Model):
    """
    Data model for all event properties stored in the datastore.

    :type starred: bool
    :type hidden: bool
    :type settings: EventSettings
    """
    starred = ndb.BooleanProperty(default=False)
    hidden = ndb.BooleanProperty(default=False)
    settings = ndb.StructuredProperty(EventSettings)


class Settings(ndb.Model):
    """Settings for a user."""
    pass
