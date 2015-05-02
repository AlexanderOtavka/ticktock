'''The endpoints server.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


import endpoints
from protorpc import remote
from google.appengine.ext import ndb
from endpoints_proto_datastore.ndb import EndpointsModel

# import auth
import models


WEB_CLIENT_ID = ''
ANDROID_CLIENT_ID = ''
ANDROID_AUDIENCE = ANDROID_CLIENT_ID
IOS_CLIENT_ID = ''


@endpoints.api(name='anticipate', version='v1',
               allowed_client_ids=[endpoints.API_EXPLORER_CLIENT_ID])
class AnticipateAPI(remote.Service):
    '''Mediates between the client and the datastore and calendar APIs.'''

    @models.Calendar.query_method(name='calendars.get', user_required=True,
                                  http_method='GET', path='calendars')
    def get_calendars(self, query):
        '''Get a list of calendars the user has chosen.'''
        return query

    @models.Calendar.query_method(name='calendars.public.get', user_required=False,
                                  http_method='GET', path='calendars/public')
    def get_public_calendars(self, query):
        '''Get a list of public calendars.'''
        return query

    @models.Calendar.query_method(name='calendars.user.get', user_required=True,
                                  http_method='GET', path='calendars/user')
    def get_user_calendars(self, query):
        '''Get all of the user's calendars for a given google account.'''
        return query

    @models.Calendar.method(name='calendars.put', user_required=True,
                            http_method='PUT', path='calendars')
    def put_calendar(self, model):
        '''Add a calendar to the user's list.'''
        return model

    @models.Calendar.method(name='calendars.post', user_required=True,
                            http_method='POST', path='calendars')
    def post_calendar(self, model):
        '''Update a calendar's data.'''
        return model

    @models.Calendar.method(name='calendars.delete', user_required=True,
                            http_method='DELETE', path='calendars')
    def delete_calendar(self, model):
        '''Remove a calendar from a user's list.'''
        return model

    @models.Event.query_method(name='events.get', user_required=False,
                               http_method='GET', path='events')
    def get_events(self, query):
        '''Get a list of events for a given calendar.'''
        return query

    @models.Event.method(name='events.post', user_required=True,
                         http_method='POST', path='events')
    def post_event(self, model):
        '''Update an event's data.'''
        return model

    @models.Settings.query_method(name='settings.get', user_required=True,
                                  http_method='GET', path='settings')
    def get_settings(self, query):
        '''Get the current user's settings data.'''
        return query

    @models.Settings.method(name='settings.post', user_required=True,
                            http_method='POST', path='settings')
    def post_settings(self, model):
        '''Change the current user's settings.'''
        return model

application = endpoints.api_server([AnticipateAPI])
