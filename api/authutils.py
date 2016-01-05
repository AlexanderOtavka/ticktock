"""
Tools for connecting to Google APIs and authenticating the user.

Some code stolen from
https://github.com/GoogleCloudPlatform/appengine-picturesque-python, and is
subject to copyright by Google.
"""

from __future__ import division, print_function

import os
import json

import endpoints
from endpoints import users_id_token
from google.appengine.api import urlfetch
from googleapiclient.discovery import build
from oauth2client import client
from httplib2 import Http
from oauth2client.appengine import CredentialsNDBModel, StorageByKeyName
from oauth2client.client import Credentials


__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


CALENDAR_API_NAME = "calendar"
CALENDAR_API_VERSION = "v3"

SERVICE_ACCOUNT_SCOPES = "https://www.googleapis.com/auth/calendar"


_SAVED_TOKEN_DICT = {}


def get_user_id():
    """
    Get the Google+ User ID from the environment.

    Attempts to get the user ID if the token in the environment is either
    an ID token or a bearer token. If there is no token in the environment
    or there the current token is invalid (no current endpoints user), will not
    attempt either.

    :rtype: unicode
    :return: The Google+ User ID of the user whose token is in the
             environment if it can be retrieved, else None.
    """
    # Assumes endpoints.get_current_user has already returned a
    # non-null value, hence the needed environment variables
    # should already be set and this won't make the RPC/url fetch
    # a second time.
    if endpoints.get_current_user() is None:
        return

    # noinspection PyProtectedMember
    token = users_id_token._get_token(None)
    if token is None:
        return

    user_id = _get_user_id_from_id_token(token)
    if user_id is None:
        user_id = _get_user_id_from_bearer_token(token)
    return user_id


def require_user_id():
    """
    Return the current user's google plus id or raise 401.

    :rtype: unicode
    :raise endpoints.UnauthorizedException: if user ID not found.
    """
    current_user_id = get_user_id()
    if current_user_id is None:
        raise endpoints.UnauthorizedException()
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


def _get_user_id_from_id_token(jwt):
    """
    Attempt to get Google+ User ID from ID Token.

    First calls endpoints.get_current_user() to assure there is a valid user.
    If it has already been called, there will be environment variables set
    so this will be a low-cost call (no network overhead).

    After this, we know the JWT is valid and can simply parse a value from it.

    :param str jwt: The JSON web token which acts as the ID Token.

    :rtype: unicode
    :return: The Google+ user ID or None if it can't be determined
             from the JWT.
    """
    if endpoints.get_current_user() is None:
        return

    segments = jwt.split('.')
    if len(segments) != 3:
        return

    # noinspection PyProtectedMember
    json_body = users_id_token._urlsafe_b64decode(segments[1])
    # noinspection PyBroadException
    try:
        parsed = json.loads(json_body)
        return parsed.get('sub')
    except:
        pass


_original_fetch = urlfetch.fetch


def _patched_urlfetch(url, *args, **kwargs):
    """
    A monkey-patched version of urlfetch.fetch which will cache results.

    We use this to cache calls to TOKENINFO so that the
    _get_user_id_from_bearer_token method doesn't need to make urlfetch that
    has already been performed.

    When GET calls (only a url, no other args) are made for a specified token,
    we check if they were made to the TOKENINFO url and save the result in
    _SAVED_TOKEN_DICT using the access_token from the request as the key.

    :param str url: To be passed to URL fetch.
    :param args: The positional args to be passed to urlfetch.fetch.
    :param kwargs: The keyword args to be passed to urlfetch.fetch.

    :return: URLFetch Response object.
    """
    result = _original_fetch(url, *args, **kwargs)
    # Only a bare call with nothing but a URL will be cached
    if not (args or kwargs):
        # noinspection PyProtectedMember
        tokeninfo_url_prefix = users_id_token._TOKENINFO_URL + '?access_token='

        # In reality we should use urlparse.parse_qs to determine
        # this value, but we rely a bit here on the underlying
        # implementation in users_id_token.py.
        if url.startswith(tokeninfo_url_prefix):
            token = url.split(tokeninfo_url_prefix, 1)[1]
            _SAVED_TOKEN_DICT[token] = result

    return result


# noinspection PyProtectedMember
_original_maybe_set = users_id_token._maybe_set_current_user_vars


def _patched_maybe_set(method, api_info=None, request=None):
    """
    Monkey patch for _maybe_set_current_user_vars which uses custom urlfetch.

    :param method: The class method that's handling this request.  This method
                   should be annotated with @endpoints.method.
    :param api_info: An api_config._ApiInfo instance. Optional. If None,
                     will attempt to parse api_info from the implicit
                     instance of the method.
    :param request: The current request, or None.
    """
    try:
        urlfetch.fetch = _patched_urlfetch
        _original_maybe_set(method, api_info=api_info, request=request)
    finally:
        urlfetch.fetch = _original_fetch


# Monkey patch the method from users_id_token
users_id_token._maybe_set_current_user_vars = _patched_maybe_set


def _get_user_id_from_bearer_token(token):
    """
    Attempts to get Google+ User ID from Bearer Token.

    First calls endpoints.get_current_user() to assure there is a valid user.
    If it has already been called, there will be environment variables set
    so this will be a low-cost call (no network overhead).

    Since we have already called endpoints.get_current_user, if the token is a
    valid Bearer token, a call to the TOKENINFO url must have been made hence a
    URLFetch response object corresponding to the token should be in
    _SAVED_TOKEN_DICT.

    :param str token: A Bearer Token.

    :rtype: unicode
    :return: The Google+ user ID or None if it can't be determined from the
             token.
    """
    if endpoints.get_current_user() is None:
        return

    urlfetch_result = _SAVED_TOKEN_DICT.get(token)
    if urlfetch_result is None:
        return

    if urlfetch_result.status_code == 200:
        # noinspection PyBroadException
        try:
            user_info = json.loads(urlfetch_result.content)
            return user_info.get('user_id')
        except:
            pass
