'''Tools for connecting to Google APIs and authenticating the user.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'



import os
import pickle
import httplib

import wrapt
import webapp2
import endpoints
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api.app_identity import get_default_version_hostname
from apiclient.discovery import build
from oauth2client import client
from oauth2client.appengine import CredentialsProperty, StorageByKeyName
from httplib2 import Http


@wrapt.decorator
def required(func, instance, args, kwargs):
    current_user = endpoints.get_current_user()
    if current_user is None:
        raise endpoints.UnauthorizedException('Invalid token.')
    return func(*args, **kwargs)

class CredentialsModel(db.Model):
    credentials = CredentialsProperty()

    @classmethod
    def get_store(cls, user_id):
        return StorageByKeyName(cls, user_id, 'credentials')

class NoStoredCredentialsError(Exception):
    def __init__(self, auth_uri):
        super(NoStoredCredentialsError, self).__init__('No credentials found in storage.')
        self.auth_uri = auth_uri

class AuthRedirectException(endpoints.ServiceException):
    http_status = httplib.BAD_REQUEST
    #http_status = httplib.CONFLICT
    #http_status = httplib.PROXY_AUTHENTICATION_REQUIRED

def get_credentials(client_secret_file, scope, user_id, redirect_uri):
    '''Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Args:
        client_secret_file (string): Path to client_secret.json.
        scopes (list of strings): Scopes to request.
        user_id (string): Google+ user id.
    Returns:
        Credentials: The obtained credential.
    Raises:
        NoStoredCredentialsError: Includes the auth_uri to point the user to.
    '''
    store = CredentialsModel.get_store(user_id)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret_file, scope,
                                              redirect_uri=redirect_uri)
        auth_uri = flow.step1_get_authorize_url()
        memcache.set(user_id, pickle.dumps(flow))
        raise NoStoredCredentialsError(auth_uri)
    return credentials

def get_calendar_service(user_id):
    '''Get a Resource object for calendar API v3 for a given user.

    Args:
        user_id (string): Google+ user id.
    Returns:
        Resource: The calendar API v3 service.
    Raises:
        AuthRedirectException: Includes auth uri in message.
    '''
    user_id = str(user_id)
    scope = 'https://www.googleapis.com/auth/calendar.readonly'
    client_secret_file = os.path.join(os.path.dirname(__file__), 'client_secret.json')
    redirect_uri = 'http://' + get_default_version_hostname() + '/oauth2/calendar/' + user_id

    try:
        credentials = get_credentials(client_secret_file, scope, user_id, redirect_uri)
    except NoStoredCredentialsError as e:
        raise AuthRedirectException(e.auth_uri)
    return build('calendar', 'v3', http=credentials.authorize(Http()))


class CalendarRedirectHandler(webapp2.RequestHandler):
    def get(self, user_id):
        code = self.request.get('code')
        flow = pickle.loads(memcache.get(user_id))
        credentials = flow.step2_exchange(code)
        store = CredentialsModel.get_store(user_id)
        store.put(credentials)
        self.response.type = 'text/html'
        self.response.write(
            '<!DOCTYPE html><html><body><script> window.close(); </script></body></html>')

redirect_handlers = webapp2.WSGIApplication([
    (r'/oauth2/calendar/(\d+)', CalendarRedirectHandler)
    ])
