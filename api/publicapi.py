"""API for accessing public calendars and events."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

import endpoints
from protorpc import remote
from oauth2client.appengine import AppAssertionCredentials

from ticktockapi import ticktock_api
import authutils
import messages
import gapiutils
import searchutils


@ticktock_api.api_class(resource_name="public", path="public",
                        auth_level=endpoints.AUTH_LEVEL.NONE)
class PublicAPI(remote.Service):
    """Access and manage public calendars."""

    @endpoints.method(messages.SearchQuery, messages.CalendarCollection,
                      name="calendars.list",
                      http_method="GET", path="calendars")
    def get_public_calendars(self, request):
        """Get a list of public calendars."""
        service = authutils.get_service(
            authutils.CALENDAR_API_NAME,
            authutils.CALENDAR_API_VERSION,
            AppAssertionCredentials(authutils.SERVICE_ACCOUNT_SCOPES)
        )
        calendars = gapiutils.get_calendars(service)

        # Sort and search
        search = request.search
        if search:
            calendars = searchutils.calendar_keyword_alpha_search(
                calendars, search)
        else:
            calendars = searchutils.calendar_alpha_sort(calendars)

        return messages.CalendarCollection(items=calendars)

    @endpoints.method(messages.EVENT_SEARCH_RESOURCE_CONTAINER,
                      messages.EventCollection,
                      name="events.list", http_method="GET",
                      path="calendars/{calendar_id}/events")
    def get_public_events(self, request):
        """Get a list of events for a given public calendar."""
        service = authutils.get_service(
            authutils.CALENDAR_API_NAME,
            authutils.CALENDAR_API_VERSION,
            AppAssertionCredentials(authutils.SERVICE_ACCOUNT_SCOPES)
        )
        events = gapiutils.get_events(service, request.calendar_id)

        # Sort and search
        search = request.search
        if search:
            events = searchutils.event_keyword_chron_search(events, search)
        else:
            events = searchutils.event_chron_sort(events)

        return messages.EventCollection(items=events)
