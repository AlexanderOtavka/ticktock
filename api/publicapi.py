"""API for accessing public calendars and events."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

import endpoints
from protorpc import remote

from ticktockapi import ticktock_api
import messages


@ticktock_api.api_class(resource_name="public",
                        path="public",
                        auth_level=endpoints.AUTH_LEVEL.NONE)
class PublicAPI(remote.Service):
    @endpoints.method(messages.SearchQuery, messages.CalendarCollection,
                      name="calendars.list",
                      http_method="GET", path="calendars")
    def get_public_calendars(self, request):
        """Get a list of public calendars."""
        # TODO: implement public calendars
        calendars = []
        return messages.CalendarCollection(items=calendars)

    @endpoints.method(messages.EVENT_SEARCH_RESOURCE_CONTAINER,
                      messages.EventCollection,
                      name="events.list", http_method="GET",
                      path="calendars/{calendar_id}/events")
    def get_public_events(self, request):
        """Get a list of events for a given public calendar."""
        # TODO: implement public events
        events = []
        return messages.EventCollection(items=events)

