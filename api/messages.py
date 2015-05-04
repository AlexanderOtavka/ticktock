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
    name = messages.StringField(3, required=True)
    start_date = message_types.DateTimeField(4, required=True)
    end_date = message_types.DateTimeField(5, required=True)
    starred = messages.BooleanField(6, default=False)
    hidden = messages.BooleanField(7, default=False)
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
    page_token = messages.StringField(4)
    # FUTURE: implement timezones
    timezone = messages.StringField(5)
