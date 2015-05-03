'''Endpoints messages.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


from protorpc import messages, message_types


class Calendar(messages.Message):
    name = messages.StringField(1, required=True)
    hidden = messages.BooleanField(2, default=False)
    color = messages.StringField(3, required=True)
    link = messages.StringField(4)

class CalendarCollection(messages.Message):
    items = messages.MessageField(Calendar, 1, repeated=True)

class EventSettings(messages.Message):
    '''Settings for an event.'''
    pass

class Event(messages.Message):
    name = messages.StringField(1, required=True)
    start_date = message_types.DateTimeField(2, required=True)
    end_date = message_types.DateTimeField(3, required=True)
    starred = messages.BooleanField(4, default=False)
    hidden = messages.BooleanField(5, default=False)
    link = messages.StringField(6)
    settings = messages.MessageField(EventSettings, 7)

class EventCollection(messages.Message):
    items = messages.MessageField(Event, 1, repeated=True)

class Settings(messages.Message):
    '''Settings for a user.'''
    pass

class SearchQuery(messages.Message):
    search = messages.StringField(1)
