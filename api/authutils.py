"""Tools for connecting to Google APIs and authenticating the user."""

import os

import endpoints
from apiclient.discovery import build
from oauth2client import client
from httplib2 import Http
from oauth2client.appengine import CredentialsNDBModel, StorageByKeyName
from oauth2client.client import Credentials
from auth_util import get_google_plus_user_id

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


CALENDAR_API_NAME = "calendar"
CALENDAR_API_VERSION = "v3"

SERVICE_ACCOUNT_SCOPES = "https://www.googleapis.com/auth/calendar"


def get_user_id():
    """
    Return the current user's google plus id.

    :rtype: unicode
    """
    return get_google_plus_user_id()


def require_user_id():
    """
    Return the current user's google plus id or raise 401.

    :rtype: unicode
    :raise endpoints.UnauthorizedException: if user ID not found.
    """
    current_user_id = get_user_id()
    if current_user_id is None:
        raise endpoints.UnauthorizedException("Invalid token.")
    return current_user_id


def get_user_credentials():
    """
    Get oauth2 credentials from the endpoints environment.

    :rtype: client.AccessTokenCredentials
    """
    if "HTTP_AUTHORIZATION" in os.environ and "HTTP_USER_AGENT" in os.environ:
        tokentype, token = os.environ["HTTP_AUTHORIZATION"].split(" ")
        user_agent = os.environ["HTTP_USER_AGENT"]
        credentials = client.AccessTokenCredentials(token, user_agent)

        assert get_user_id() is not None
        store = StorageByKeyName(CredentialsNDBModel, get_user_id(),
                                 "credentials")
        store.put(credentials)

        return credentials
    else:
        return None


def get_service(api_name, api_version, credentials=None):
    """
    Get a resource object for a given api using given credentials.

    :type api_name: str
    :type api_version: str
    :type credentials: Credentials
    :return: Resource object.
    """
    credentials = credentials or get_user_credentials()
    if credentials is None or credentials.invalid:
        return None
    else:
        return build(api_name, api_version, http=credentials.authorize(Http()))
