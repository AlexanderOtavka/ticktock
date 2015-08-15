"""Tools for connecting to Google APIs and authenticating the user."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

import os

import endpoints
from apiclient.discovery import build
from oauth2client import client
from httplib2 import Http

import gapiutils


def auth_required(func):
    """Decorator to make given endpoints method require signin.

    :type func: (T, U) -> V
    :rtype: (T, U) -> V
    """
    def wrapper(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            raise endpoints.UnauthorizedException("Invalid token.")
        return func(self, request)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# class CredentialsModel(db.Model):
#     """
#     A db model for storing oauth2 credentials.
#
#     :type credentials: client.Credentials
#     """
#     credentials = CredentialsProperty()
#
#     @classmethod
#     def get_store(cls, user_id):
#         """
#         Get a storage object for a credentials model for a given user id.
#
#         :type user_id: str
#         :rtype: StorageByKeyName
#         """
#         return StorageByKeyName(cls, user_id, "credentials")
#
#
# class NoStoredCredentialsError(Exception):
#     def __init__(self, auth_uri):
#         super(NoStoredCredentialsError, self).__init__(
#             "No credentials found in storage.")
#         self.auth_uri = auth_uri
#
#
# class AuthRedirectException(endpoints.ServiceException):
#     http_status = httplib.BAD_REQUEST
#     # http_status = httplib.CONFLICT
#     # http_status = httplib.PROXY_AUTHENTICATION_REQUIRED


def get_credentials():
    if "HTTP_AUTHORIZATION" in os.environ and "HTTP_USER_AGENT" in os.environ:
        tokentype, token = os.environ["HTTP_AUTHORIZATION"].split(" ")
        user_agent = os.environ["HTTP_USER_AGENT"]
        return client.AccessTokenCredentials(token, user_agent)
    return None


def get_service_from_credentials(api_name, api_version, credentials):
    """
    Get a resource object for a given api using given credentials.

    :type api_name: str
    :type api_version: str
    :type credentials: client.OAuth2Credentials
    """
    if credentials is None or credentials.invalid:
        return None
    return build(api_name, api_version, http=credentials.authorize(Http()))


def get_calendar_service():
    """Get a Resource object for calendar API v3 for a given user."""
    return get_service_from_credentials(gapiutils.CALENDAR_API_NAME,
                                        gapiutils.CALENDAR_API_VERSION,
                                        get_credentials())
