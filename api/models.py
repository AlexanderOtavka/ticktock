"""Datastore models."""

from google.appengine.ext import ndb

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


USER_KIND = "User"


def get_user_key(user_id):
    """
    Get an ndb key for a user based on a user id.

    :type user_id: unicode
    :rtype: ndb.Key
    """
    return ndb.Key(USER_KIND, int(user_id) % (1 << 48))


def get_user_query():
    """Get an ndb query with kind='User'."""
    return ndb.Query(kind=USER_KIND)


class Calendar(ndb.Model):
    """
    Data model for all calendar properties stored in the datastore.

    :type hidden: bool
    """
    hidden = ndb.BooleanProperty()


class EventSettings(ndb.Model):
    """
    Data model for and event's settings.

    Choose whether to show a countdown to the start of the event, or to the end
    of the event, or both, but not neither.  That would be the same as hiding.

    :type count_to_start: bool
    :type count_to_end: bool
    """
    count_to_start = ndb.BooleanProperty(default=True)
    count_to_end = ndb.BooleanProperty(default=False)


class Event(ndb.Model):
    """
    Data model for all event properties stored in the datastore.

    :type starred: bool
    :type hidden: bool
    :type settings: EventSettings
    """
    starred = ndb.BooleanProperty()
    hidden = ndb.BooleanProperty()
    settings = ndb.StructuredProperty(EventSettings)


class Settings(ndb.Model):
    """Settings for a user."""
    pass
