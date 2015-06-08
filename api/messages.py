'''Endpoints messages.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


from protorpc import messages, message_types


class Calendar(messages.Message):
    calendar_id = messages.StringField(1, required=True)
    name = messages.StringField(2)
    hidden = messages.BooleanField(3)
    color = messages.StringField(4)
    link = messages.StringField(5)

class CalendarCollection(messages.Message):
    items = messages.MessageField(Calendar, 1, repeated=True)
    next_page_token = messages.StringField(2)

class EventSettings(messages.Message):
    '''Settings for an event.'''
    pass

class Event(messages.Message):
    event_id = messages.StringField(1, required=True)
    calendar_id = messages.StringField(2, required=True)
    name = messages.StringField(3)
    start_date = message_types.DateTimeField(4)
    end_date = message_types.DateTimeField(5)
    starred = messages.BooleanField(6)
    hidden = messages.BooleanField(7)
    link = messages.StringField(8)
    settings = messages.MessageField(EventSettings, 9)

class EventCollection(messages.Message):
    items = messages.MessageField(Event, 1, repeated=True)
    next_page_token = messages.StringField(2)

class Settings(messages.Message):
    '''Settings for a user.'''
    pass

class SearchQuery(messages.Message):
    '''A search query with generic filters.

    Fields:
        search (string): A generic search string.
        calendar_id (string): For event searches, narrow by calendar_id.
        only_hidden (boolean): For event searches, either show only hidden, or show no hidden.
        page_token (string): For queries to large data sets.
        timezone (string): For event searches, not yet implemented.
    '''
    search = messages.StringField(1)
    calendar_id = messages.StringField(2)
    only_hidden = messages.BooleanField(3)
    # TODO: implement paging (get all the data for forever, then memcache it)
    page_token = messages.StringField(4)
    # FUTURE: implement timezones.
    timezone = messages.StringField(5)
