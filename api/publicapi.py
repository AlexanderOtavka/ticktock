"""API for accessing public calendars and events."""

from __future__ import division, print_function

import urllib2

import endpoints
from protorpc import remote
from oauth2client.appengine import AppAssertionCredentials

from ticktockapi import ticktock_api
import authutils
import messages
import gapiutils
import searchutils

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


@ticktock_api.api_class(resource_name="public", path="public",
                        auth_level=endpoints.AUTH_LEVEL.NONE)
class PublicAPI(remote.Service):
    """Access and manage public calendars."""

    # TODO: add method for adding public calendars

    @endpoints.method(messages.CALENDAR_SEARCH_RESOURCE,
                      messages.CalendarCollection,
                      name="calendars.list",
                      http_method="GET", path="calendars")
    def calendars_list(self, request):
        """
        Get a list of public calendars.

        :type request: messages.CALENDAR_SEARCH_RESOURCE
        """
        service = authutils.get_service(
            authutils.CALENDAR_API_NAME,
            authutils.CALENDAR_API_VERSION,
            AppAssertionCredentials(authutils.SERVICE_ACCOUNT_SCOPES)
        )
        calendars = gapiutils.get_calendars(service)

        # Sort and search
        # TODO: sort by number of people following the calendar
        search = request.search
        if search:
            calendars = searchutils.calendar_keyword_alpha_search(
                calendars, search)
        else:
            calendars = searchutils.calendar_alpha_sort(calendars)

        return messages.CalendarCollection(items=calendars)

    @endpoints.method(messages.EVENT_SEARCH_RESOURCE,
                      messages.EventCollection,
                      name="events.list",
                      http_method="GET", path="calendars/{calendarId}/events")
    def events_list(self, request):
        """
        Get a list of events for a given public calendar.

        :type request: messages.EVENT_SEARCH_RESOURCE
        """
        request.calendarId = urllib2.unquote(request.calendarId)

        service = authutils.get_service(
            authutils.CALENDAR_API_NAME,
            authutils.CALENDAR_API_VERSION,
            AppAssertionCredentials(authutils.SERVICE_ACCOUNT_SCOPES)
        )
        events, next_page_token = gapiutils.get_events(
                service, request.calendarId, request.timeZone,
                request.pageToken, request.maxResults)

        # Sort and search
        search = request.search
        if search:
            events = searchutils.event_keyword_search(events, search)
            events = searchutils.event_keyword_chron_sort(events, search)
        else:
            events = searchutils.event_chron_sort(events)

        return messages.EventCollection(items=events)
