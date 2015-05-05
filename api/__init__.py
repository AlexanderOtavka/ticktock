'''The endpoints server.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


import logging

import endpoints
from protorpc import remote, message_types
from google.appengine.ext import ndb
#from endpoints_proto_datastore.ndb import EndpointsModel
from auth_util import get_google_plus_user_id

import auth
import messages
import models
import calendar_api


SCOPES = [
    #'https://www.googleapis.com/auth/plus.profile.emails.read',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/plus.me',
]
WEB_CLIENT_ID = ''
ANDROID_CLIENT_ID = ''
ANDROID_AUDIENCE = ANDROID_CLIENT_ID
IOS_CLIENT_ID = ''
ALLOWED_CLIENT_IDS = [
    endpoints.API_EXPLORER_CLIENT_ID,
]


@endpoints.api(name='anticipate', version='v1', scopes=SCOPES,
               allowed_client_ids=ALLOWED_CLIENT_IDS)
class AnticipateAPI(remote.Service):
    '''Mediates between the client and the datastore and calendar APIs.'''

    @endpoints.method(message_types.VoidMessage, messages.CalendarCollection,
                      name='calendars.get', http_method='GET', path='calendars')
    @auth.required
    def get_calendars(self, request):
        '''Get a list of calendars the user has chosen.'''
        user_id = get_google_plus_user_id()
        service = auth.get_calendar_service(user_id)
        all_calendars = (calendar_api.get_personal_calendars(service) +
                         calendar_api.get_public_calendars())

        user_key = models.get_user_key(user_id)
        chosen_ndb = models.Calendar.query(ancestor=user_key).fetch()
        chosen_calendars = []
        for entity in chosen_ndb:
            for cal in all_calendars:
                if cal.calendar_id == entity.key.string_id():
                    cal.hidden = entity.hidden
                    chosen_calendars.append(cal)
                    break
            else:
                logging.info('Deleted: unbound Calendar entity with calendar_id = "{}" and ' +
                             'user_id = "{}".'.format(entity.key.string_id(), user_id))
                entity.key.delete()

        return messages.CalendarCollection(items=chosen_calendars)

    @endpoints.method(messages.SearchQuery, messages.CalendarCollection,
                      name='calendars.public.get', http_method='GET', path='calendars/public')
    def get_public_calendars(self, request):
        '''Get a list of public calendars.'''
        calendars = calendar_api.get_public_calendars()
        return messages.CalendarCollection(items=calendars)

    @endpoints.method(messages.SearchQuery, messages.CalendarCollection,
                      name='calendars.personal.get', http_method='GET', path='calendars/personal')
    @auth.required
    def get_personal_calendars(self, request):
        '''Get all of the user's personal calendars for a given google account.'''
        user_id = get_google_plus_user_id()
        service = auth.get_calendar_service(user_id)
        calendars = calendar_api.get_personal_calendars(service)
        return messages.CalendarCollection(items=calendars)

    @endpoints.method(messages.Calendar, message_types.VoidMessage,
                      name='calendars.post', http_method='POST', path='calendars')
    @auth.required
    def post_calendar(self, request):
        '''Add a calendar to the user's list.'''
        user_id = get_google_plus_user_id()
        cal_id = request.calendar_id
        user_key = models.get_user_key(user_id)
        model = models.Calendar(id=cal_id, parent=user_key)
        model.put()
        return message_types.VoidMessage()

    @endpoints.method(messages.Calendar, messages.Calendar,
                      name='calendars.patch', http_method='PATCH', path='calendars')
    @auth.required
    def patch_calendar(self, request):
        '''Update a calendar's data.

        Only Calendar.hidden can be changed.
        '''
        user_id = get_google_plus_user_id()
        cal_id = request.calendar_id
        user_key = models.get_user_key(user_id)
        model = ndb.Key(models.Calendar, cal_id, parent=user_key).get()
        if model is None:
            raise endpoints.ForbiddenException(
                'No calendar with id of "{}" in user\'s list.'.format(cal_id))

        temp = request.hidden
        if temp is not None:
            model.hidden = temp
        model.put()
        return messages.Calendar(
            calendar_id=cal_id,
            hidden=model.hidden,
        )

    @endpoints.method(messages.Calendar, messages.Calendar,
                      name='calendars.delete', http_method='DELETE', path='calendars')
    @auth.required
    def delete_calendar(self, request):
        '''Remove a calendar from a user's list.'''
        user_id = get_google_plus_user_id()
        cal_id = request.calendar_id
        user_key = models.get_user_key(user_id)
        key = ndb.Key(models.Calendar, cal_id, parent=user_key)
        entity = key.get()
        key.delete()
        return messages.Calendar(
            calendar_id=cal_id,
            hidden = entity.hidden,
        )

    @endpoints.method(messages.SearchQuery, messages.EventCollection,
                      name='events.get', http_method='GET', path='events')
    @auth.required
    def get_events(self, request):
        '''Get a list of events for a given calendar.

        If no calendar is given, events from all of the user's calendars will be shown.
        '''
        user_id = get_google_plus_user_id()
        user_key = models.get_user_key(user_id)
        service = auth.get_calendar_service(user_id)

        cal_id = request.calendar_id
        if cal_id:
            events = calendar_api.get_events(service, cal_id)
        else:
            events = []
            hidden = request.only_hidden
            if hidden is None:
                hidden = False
            query = models.Calendar.query(models.Calendar.hidden == hidden, ancestor=user_key)
            for calendar in query.fetch():
                events += calendar_api.get_events(service, calendar.key.string_id())

        for event in events:
            key = ndb.Key(models.Event, event.event_id,
                          parent=ndb.Key(models.Calendar, event.calendar_id, parent=user_key))
            entity = key.get()
            if entity is not None:
                event.hidden = entity.hidden
                event.starred = entity.starred

        return messages.EventCollection(items=events)

    @endpoints.method(messages.SearchQuery, messages.EventCollection,
                      name='events.public.get', http_method='GET', path='events/public')
    def get_public_events(self, request):
        '''Get a list of events for a given public calendar.'''
        events = []
        return messages.EventCollection(items=events)

    @endpoints.method(messages.Event, messages.Event,
                      name='events.patch', http_method='PATCH', path='events')
    @auth.required
    def patch_event(self, request):
        '''Update an event's data.

        Only Event.hidden and Event.starred can be changed.  An event cannot be starred if it is
        hidden.
        '''
        user_id = get_google_plus_user_id()
        cal_id = request.calendar_id
        event_id = request.event_id
        user_key = models.get_user_key(user_id)
        cal_key = ndb.Key(models.Calendar, cal_id, parent=user_key)
        if cal_key.get() is None:
            raise endpoints.ForbiddenException(
                'No calendar with id of "{}" in user\'s list.'.format(cal_id))

        model = ndb.Key(models.Event, event_id, parent=cal_key).get()
        if model is None:
            model = models.Event(id=event_id, parent=cal_key)

        hidden = request.hidden
        starred = request.starred
        if hidden is not None:
            model.hidden = hidden
        if model.hidden:
            starred = False
        if starred is not None:
            model.starred = starred

        model.put()
        return messages.Event(
            event_id=event_id,
            calendar_id=cal_id,
            hidden=model.hidden,
            starred=model.starred,
        )

    @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                      name='settings.get', http_method='GET', path='settings')
    @auth.required
    def get_settings(self, request):
        '''Get the current user's settings data.'''
        raise NotImplementedError()

    @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                      name='settings.patch', http_method='PATCH', path='settings')
    @auth.required
    def patch_settings(self, request):
        '''Change the current user's settings.'''
        raise NotImplementedError()

application = endpoints.api_server([AnticipateAPI])
