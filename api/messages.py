"""Endpoints messages."""

from datetime import datetime

from protorpc import messages, message_types
import endpoints

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


class CalendarProperties(messages.Message):
    """
    Data for all properties of a calendar.

    :type calendarId: str
    :type name: str
    :type hidden: bool
    :type color: str
    :type link: str
    """
    calendarId = messages.StringField(1, required=True)
    name = messages.StringField(2)
    hidden = messages.BooleanField(3)
    color = messages.StringField(4)
    link = messages.StringField(5)


class CalendarWriteProperties(messages.Message):
    """
    Data for writeable properties of a calendar.

    :type hidden: bool
    """
    hidden = messages.BooleanField(1)

CALENDAR_ID_RESOURCE = endpoints.ResourceContainer(
        message_types.VoidMessage,
        calendarId=messages.StringField(1, variant=messages.Variant.STRING,
                                        required=True))
CALENDAR_WRITE_RESOURCE = endpoints.ResourceContainer(
        CalendarWriteProperties,
        calendarId=messages.StringField(2, variant=messages.Variant.STRING,
                                        required=True))


class CalendarCollection(messages.Message):
    """
    Non-pageable array of calendar messages.

    :type items: list[Calendar]
    """
    items = messages.MessageField(CalendarProperties, 1, repeated=True)


class EventSettings(messages.Message):
    """
    Settings for an event.

    Choose whether to show a countdown to the start of the event, or to the end
    of the event, or both, but not neither.  That would be the same as hiding.

    :type countToStart: bool
    :type countToEnd: bool
    """
    # TODO: implement settings for events
    countToStart = messages.BooleanField(1, default=True)
    countToEnd = messages.BooleanField(2, default=False)


class EventProperties(messages.Message):
    """
    Data for all properties of events.

    :type eventId: str
    :type calendarId: str
    :type name: str
    :type startDate: datetime
    :type endDate: datetime
    :type starred: bool
    :type hidden: bool
    :type link: str
    :type settings: EventSettings
    :type recurrenceId: str
    """
    eventId = messages.StringField(1, required=True)
    calendarId = messages.StringField(2, required=True)
    name = messages.StringField(3)
    startDate = message_types.DateTimeField(4, required=True)
    endDate = message_types.DateTimeField(5, required=True)
    starred = messages.BooleanField(6, required=True)
    hidden = messages.BooleanField(7, required=True)
    link = messages.StringField(8, required=True)
    settings = messages.MessageField(EventSettings, 9)
    recurrenceId = messages.StringField(10)


class EventWriteProperties(messages.Message):
    """
    Data for writeable properties of events.

    :type starred: bool
    :type hidden: bool
    :type settings: EventSettings
    """
    starred = messages.BooleanField(1)
    hidden = messages.BooleanField(2)
    settings = messages.MessageField(EventSettings, 3)

EVENT_ID_RESOURCE = endpoints.ResourceContainer(
        message_types.VoidMessage,
        eventId=messages.StringField(1, variant=messages.Variant.STRING,
                                     required=True),
        calendarId=messages.StringField(2, variant=messages.Variant.STRING,
                                        required=True))
EVENT_WRITE_RESOURCE = endpoints.ResourceContainer(
        EventWriteProperties,
        eventId=messages.StringField(4, variant=messages.Variant.STRING,
                                     required=True),
        calendarId=messages.StringField(5, variant=messages.Variant.STRING,
                                        required=True))


class EventCollection(messages.Message):
    """
    Pageable array of event messages.

    :type items: list[Event]
    :type nextPageToken: str
    """
    items = messages.MessageField(EventProperties, 1, repeated=True)
    nextPageToken = messages.StringField(2)


_SEARCH_QUERY_FIELDS = dict(
        search=messages.StringField(1, variant=messages.Variant.STRING),
        hidden=messages.BooleanField(2, variant=messages.Variant.BOOL))
EVENT_SEARCH_RESOURCE = endpoints.ResourceContainer(
        message_types.VoidMessage,
        # TODO: implement timezones.
        timezone=messages.StringField(3, variant=messages.Variant.STRING),
        pageToken=messages.StringField(4, variant=messages.Variant.STRING),
        calendarId=messages.StringField(5, variant=messages.Variant.STRING,
                                        required=True),
        **_SEARCH_QUERY_FIELDS)
CALENDAR_SEARCH_RESOURCE = endpoints.ResourceContainer(
        message_types.VoidMessage,
        **_SEARCH_QUERY_FIELDS)
