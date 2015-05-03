'''The endpoints server.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


import endpoints
from protorpc import remote, message_types
# from google.appengine.ext import ndb
# from endpoints_proto_datastore.ndb import EndpointsModel
from auth_util import get_google_plus_user_id

import auth
import messages
import models
from oauth2 import get_calendar_service


WEB_CLIENT_ID = ''
ANDROID_CLIENT_ID = ''
ANDROID_AUDIENCE = ANDROID_CLIENT_ID
IOS_CLIENT_ID = ''
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    # 'https://www.googleapis.com/auth/plus.profile.emails.read',
    'https://www.googleapis.com/auth/plus.me',
    ]
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
        return request

    @endpoints.method(messages.SearchQuery, messages.CalendarCollection,
                      name='calendars.public.get', http_method='GET', path='calendars/public')
    def get_public_calendars(self, request):
        '''Get a list of public calendars.'''
        return request

    @endpoints.method(messages.SearchQuery, messages.CalendarCollection,
                      name='calendars.user.get', http_method='GET', path='calendars/user')
    @auth.required
    def get_user_calendars(self, request):
        '''Get all of the user's calendars for a given google account.'''
        service = get_calendar_service(get_google_plus_user_id())
        calendar_list = service.calendarList().list(pageToken=None).execute()
        return messages.CalendarCollection(items=[
                messages.Calendar(
                    name=item['summary'],
                    color=item['backgroundColor'])
                for item in calendar_list['items']])

    @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                      name='calendars.post', http_method='POST', path='calendars')
    @auth.required
    def post_calendar(self, request):
        '''Add a calendar to the user's list.'''
        pass

    @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                      name='calendars.put', http_method='PUT', path='calendars')
    @auth.required
    def put_calendar(self, request):
        '''Update a calendar's data.'''
        pass

    @endpoints.method(message_types.VoidMessage, message_types.VoidMessage,
                      name='calendars.delete', http_method='DELETE', path='calendars')
    @auth.required
    def delete_calendar(self, request):
        '''Remove a calendar from a user's list.'''
        pass

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
