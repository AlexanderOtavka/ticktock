"""Datastore models."""

import hashlib

from google.appengine.ext import ndb
import pytz

import messages

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

    def __str__(self):
        return str(self.count_to_start) + str(self.count_to_end)


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


class EventCache(ndb.Model):
    """
    Data model for a cached event.

    :type event_id: str
    :type calendar_id: str
    :type name: str
    :type start_date: datetime
    :type end_date: datetime
    :type starred: bool
    :type hidden: bool
    :type link: str
    :type settings: EventSettings
    :type recurrence_id: str
    """
    event_id = ndb.StringProperty(required=True, indexed=False)
    calendar_id = ndb.StringProperty(required=True, indexed=False)
    name = ndb.StringProperty(indexed=False)
    start_date = ndb.DateTimeProperty(required=True, indexed=False)
    end_date = ndb.DateTimeProperty(required=True, indexed=False)
    starred = ndb.BooleanProperty(required=True, indexed=False)
    hidden = ndb.BooleanProperty(required=True, indexed=False)
    link = ndb.StringProperty(required=True, indexed=False)
    settings = ndb.StructuredProperty(EventSettings, indexed=False)
    recurrence_id = ndb.StringProperty(indexed=False)

    @classmethod
    def from_message(cls, message):
        return cls(
            event_id=message.eventId,
            calendar_id=message.calendarId,
            name=message.name,
            start_date=message.startDate.astimezone(pytz.utc).replace(
                    tzinfo=None),
            end_date=message.endDate.astimezone(pytz.utc).replace(tzinfo=None),
            starred=message.starred,
            hidden=message.hidden,
            link=message.link,
            settings=EventSettings(
                count_to_start=message.settings.countToStart,
                count_to_end=message.settings.countToEnd
            ) if message.settings is not None else None,
            recurrence_id=message.recurrenceId,
        )

    def to_message(self, time_zone):
        """
        Convert to messages.EventProperties.

        :type time_zone: str
        :rtype: messages.EventProperties
        """
        tzinfo = pytz.timezone(time_zone)
        return messages.EventProperties(
            eventId=self.event_id,
            calendarId=self.calendar_id,
            name=self.name,
            startDate=tzinfo.localize(self.start_date),
            endDate=tzinfo.localize(self.end_date),
            starred=self.starred,
            hidden=self.hidden,
            link=self.link,
            settings=EventSettings(
                countToStart=self.settings.count_to_start,
                countToEnd=self.settings.count_to_end
            ) if self.settings is not None else None,
            recurrenceId=self.recurrence_id
        )

    def __str__(self):
        string = ""
        for i in zip(*sorted(self.to_dict().iteritems()))[1]:
            string += str(i)
        return string


class EventCacheGroup(ndb.Model):
    """
    Data model for container of cached event list.

    :type unique_hash: str
    :type sequence_hash: str
    :type next_page_token: str
    :type items: list[EventCache]
    """
    unique_hash = ndb.BlobProperty(indexed=True)
    sequence_hash = ndb.BlobProperty(indexed=False)
    next_page_token = ndb.StringProperty(indexed=False)
    items = ndb.StructuredProperty(EventCache, repeated=True, indexed=False)
    extra_starred_ids = ndb.StringProperty(repeated=True, indexed=False)

    @staticmethod
    def _get_hash_from_array(array):
        """
        Generate a byte string hash from given array.

        :type array: collections.Iterable
        :rtype: str
        """
        string = ""
        for i in array:
            string += str(i)
        return hashlib.sha1(string).digest()

    @staticmethod
    def get_sequence_hash(request):
        """
        Generate hash for validating next request.

        :type request: messages.EVENT_SEARCH_RESOURCE
        :rtype: str
        """
        return EventCacheGroup._get_hash_from_array(
                (request.search, request.hidden, request.timeZone,
                 request.maxResults, request.calendarId))

    def _get_unique_hash(self, request):
        """
        Generate unique hash to find identical items.

        :type request: messages.EVENT_SEARCH_RESOURCE
        :rtype: str
        """
        return EventCacheGroup._get_hash_from_array(
                (request.search, request.hidden, request.timeZone,
                 request.maxResults, request.calendarId,
                 self.next_page_token) +
                tuple(self.items) + tuple(self.extra_starred_ids))

    def generate_hashes(self, request):
        """
        Set unique_hash and sequence_hash for this entity.

        :type request: messages.EVENT_SEARCH_RESOURCE
        """
        self.unique_hash = self._get_unique_hash(request)
        self.sequence_hash = self.get_sequence_hash(request)


class Settings(ndb.Model):
    """Settings for a user."""
    pass
