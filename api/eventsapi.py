"""API for managing events."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

import endpoints
from google.appengine.ext import ndb
from protorpc import remote

from ticktockapi import ticktock_api
import messages
import models
import authutils
import gapiutils
import searchutils


@ticktock_api.api_class(resource_name="events",
                        path="calendars/{calendar_id}/events",
                        auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class EventsAPI(remote.Service):
    """Manage events."""

    @endpoints.method(messages.EVENT_SEARCH_RESOURCE_CONTAINER,
                      messages.EventCollection,
                      name="list",
                      http_method="GET", path="/calendars/{calendar_id}/events")
    def get_events(self, request):
        """
        Get a list of events for a given calendar.

        If no calendar is given, events from all of the user's calendars will
        be shown.
        """
        # NOTE: ensure events.list works with repeating events
        user_id = authutils.require_user_id()

        user_key = models.get_user_key(user_id)
        service = authutils.get_service(gapiutils.CALENDAR_API_NAME,
                                        gapiutils.CALENDAR_API_VERSION)
        hidden = request.only_hidden
        if hidden is None:
            hidden = False

        # get event list from the google api
        cal_id = request.calendar_id
        if cal_id:
            events = gapiutils.get_events(service, cal_id)
        else:
            events = []
            query = models.Calendar.query(models.Calendar.hidden == hidden,
                                          ancestor=user_key)
            for calendar in query.fetch():
                events += gapiutils.get_events(service,
                                               calendar.key.string_id())

        # update event list with fields stored in the datastore
        for event in events:
            cal_key = ndb.Key(models.Calendar, event.calendar_id,
                              parent=user_key)
            event_key = ndb.Key(models.Event, event.event_id, parent=cal_key)
            entity = event_key.get()
            if entity is not None:
                event.hidden = entity.hidden
                event.starred = entity.starred

        # insert any starred events not included
        query = models.Event.query(models.Event.starred is True,
                                   ancestor=user_key)
        for entity in query.fetch():
            entity_id = entity.key.string_id()
            for event in events:
                if event.event_id == entity_id:
                    break
            else:
                try:
                    event = gapiutils.get_event(service,
                                                entity.key.parent().string_id(),
                                                entity_id)
                except gapiutils.OldEventError:
                    continue
                event.starred = True
                events.append(event)

        # sort and search
        search = request.search
        if search:
            events = searchutils.keyword_chron_search(events, search)
        else:
            events = searchutils.chron_sort(events)

        return messages.EventCollection(items=events)

    @endpoints.method(messages.EVENT_RESOURCE_CONTAINER,
                      messages.EventProperties,
                      name="patch", http_method="PATCH", path="{event_id}")
    def patch_event(self, request):
        """
        Update an event's data.

        Only Event.hidden and Event.starred can be changed.  An event cannot be
        starred if it is hidden.
        """
        user_id = authutils.require_user_id()

        cal_id = request.calendar_id
        event_id = request.event_id
        user_key = models.get_user_key(user_id)
        cal_key = ndb.Key(models.Calendar, cal_id, parent=user_key)
        if cal_key.get() is None:
            raise endpoints.NotFoundException(
                "No calendar with id of \"{}\" in user's list.".format(cal_id))

        model = ndb.Key(models.Event, event_id, parent=cal_key).get()
        if model is None:
            model = models.Event(id=event_id, parent=cal_key)

        hidden = request.hidden
        starred = request.starred
        if hidden is not None:
            model.hidden = hidden
        if model.hidden:
            starred = False
        if starred is not None:
            model.starred = starred

        model.put()
        return messages.EventProperties(
            event_id=event_id,
            calendar_id=cal_id,
            hidden=model.hidden,
            starred=model.starred,
        )
