"""Tools for connecting to Google APIs and authenticating the user."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

import os
import pickle
import httplib

import webapp2
import endpoints
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api.app_identity import get_default_version_hostname
from apiclient.discovery import build
from oauth2client import client
from oauth2client.appengine import CredentialsProperty, StorageByKeyName
from httplib2 import Http
import gapiutils


def auth_required(func):
    """Decorator to make given endpoints method require signin.

    :type func: (T, U) -> V
    :rtype: (T, U) -> V
    """

    def wrapped(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            raise endpoints.UnauthorizedException("Invalid token.")
        return func(self, request)

    wrapped.__name__ = func.__name__
    wrapped.__doc__ = func.__doc__
    return wrapped


class CredentialsModel(db.Model):
    """
    A db model for storing oauth2 credentials.

    :type credentials: client.Credentials
    """
    credentials = CredentialsProperty()

    @classmethod
    def get_store(cls, user_id):
        """
        Get a storage object for a credentials model for a given user id.

        :type user_id: str
        :rtype: StorageByKeyName
        """
        return StorageByKeyName(cls, user_id, "credentials")


class NoStoredCredentialsError(Exception):
    def __init__(self, auth_uri):
        super(NoStoredCredentialsError, self).__init__(
            "No credentials found in storage.")
        self.auth_uri = auth_uri


class AuthRedirectException(endpoints.ServiceException):
    http_status = httplib.BAD_REQUEST
    # http_status = httplib.CONFLICT
    # http_status = httplib.PROXY_AUTHENTICATION_REQUIRED


def get_credentials(client_secret_file, scope, user_id, redirect_uri):
    """
    Get valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    :type client_secret_file: str
    :type scope: str
    :type user_id: str
    :type redirect_uri: str
    :rtype: client.OAuth2Credentials
    :raise NoStoredCredentialsError: Includes the auth_uri to point the user to.
    """
    store = CredentialsModel.get_store(user_id)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret_file, scope,
                                              redirect_uri=redirect_uri)
        auth_uri = flow.step1_get_authorize_url()
        memcache.set(user_id, pickle.dumps(flow))
        raise NoStoredCredentialsError(auth_uri)
    return credentials


def get_service_from_credentials(api_name, api_version, credentials):
    """
    Get a resource object for a given api using given credentials.

    :type api_name: str
    :type api_version: str
    :type credentials: client.OAuth2Credentials
    """
    return build(api_name, api_version, http=credentials.authorize(Http()))


def get_calendar_service(user_id):
    """
    Get a Resource object for calendar API v3 for a given user.

    :type user_id: unicode
    :raise AuthRedirectException: Includes auth uri in message.
    """
    user_id = str(user_id)
    scope = "https://www.googleapis.com/auth/calendar.readonly"
    client_secret_file = os.path.join(os.path.dirname(__file__),
                                      "client_secret.json")
    redirect_uri = ("http://" + get_default_version_hostname() +
                    "/oauth2/calendar/" + user_id)

    try:
        credentials = get_credentials(client_secret_file, scope, user_id,
                                      redirect_uri)
    except NoStoredCredentialsError as e:
        raise AuthRedirectException(e.auth_uri)
    return get_service_from_credentials(gapiutils.API_NAME,
                                        gapiutils.API_VERSION,
                                        credentials)


class CalendarRedirectHandler(webapp2.RequestHandler):
    """Handle oauth2 redirects for calendar api requests."""

    def get(self, user_id):
        code = self.request.get("code")
        flow = pickle.loads(memcache.get(user_id))
        credentials = flow.step2_exchange(code)
        store = CredentialsModel.get_store(user_id)
        store.put(credentials)
        self.response.type = "text/html"
        self.response.write(
            "<!doctype html>" +
            "<html><body><script>" +
            "window.close();" +
            "</script></body></html>")


redirect_handlers = webapp2.WSGIApplication([
    (r"/oauth2/calendar/(\d+)", CalendarRedirectHandler),
])
