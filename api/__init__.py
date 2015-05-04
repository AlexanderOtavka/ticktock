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
from oauth2 import get_calendar_service
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
        service = get_calendar_service(user_id)
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
                logging.warning('Bad entity with id of "{}".  Deleting...'
                                .format(entity.key.string_id()))
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
        service = get_calendar_service(user_id)
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
                      name='calendars.put', http_method='PUT', path='calendars')
    @auth.required
    def put_calendar(self, request):
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

        model.hidden = request.hidden
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

    @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                      name='events.get', http_method='GET', path='events')
    def get_events(self, request):
        '''Get a list of events for a given calendar.'''
        pass

    @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                      name='events.put', http_method='PUT', path='events')
    @auth.required
    def put_event(self, request):
        '''Update an event's data.'''
        pass

    @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                      name='settings.get', http_method='GET', path='settings')
    @auth.required
    def get_settings(self, request):
        '''Get the current user's settings data.'''
        pass

    @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                      name='settings.put', http_method='PUT', path='settings')
    @auth.required
    def put_settings(self, request):
        '''Change the current user's settings.'''
        pass

application = endpoints.api_server([AnticipateAPI])
