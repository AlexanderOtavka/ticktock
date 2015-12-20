"""API for managing events."""

import endpoints
from google.appengine.ext import ndb
from protorpc import remote

from ticktockapi import ticktock_api
import messages
import models
import authutils
import gapiutils
import searchutils

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


@ticktock_api.api_class(resource_name="events",
                        path="calendars/{calendar_id}/events",
                        auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class EventsAPI(remote.Service):
    """Manage events."""

    @endpoints.method(messages.EVENT_SEARCH_RESOURCE, messages.EventCollection,
                      http_method="GET", path="/calendars/{calendar_id}/events")
    def list(self, request):
        """
        Get a list of events for a given calendar.

        If no calendar is given, events from all of the user's calendars will
        be shown.

        :type request: messages.EVENT_SEARCH_RESOURCE
        """
        user_id = authutils.require_user_id()

        user_key = models.get_user_key(user_id)
        service = authutils.get_service(authutils.CALENDAR_API_NAME,
                                        authutils.CALENDAR_API_VERSION)
        hidden = request.only_hidden
        if hidden is None:
            hidden = False

        # Get event list from the google api
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

        # Update event list with fields stored in the datastore
        for event in events:
            cal_key = ndb.Key(models.Calendar, event.calendar_id,
                              parent=user_key)
            event_key = ndb.Key(models.Event, event.event_id, parent=cal_key)
            event_entity = event_key.get()

            if event_entity is not None:
                event.hidden = event_entity.hidden
                event.starred = event_entity.starred
            elif event.recurrence_id is not None:
                recurrence_entity = ndb.Key(
                    models.Event, event.recurrence_id, parent=cal_key).get()
                if recurrence_entity is not None:
                    event.hidden = recurrence_entity.hidden
                    event.starred = recurrence_entity.starred

        # Insert any starred events not included
        # noinspection PyPep8
        query = models.Event.query(models.Event.starred == True,
                                   ancestor=user_key)
        for event_entity in query.fetch():
            entity_id = event_entity.key.string_id()
            for event in events:
                if event.event_id == entity_id:
                    break
            else:
                try:
                    event = gapiutils.get_event(
                        service, event_entity.key.parent().string_id(),
                        entity_id)
                except gapiutils.OldEventError:
                    continue
                event.starred = True
                events.append(event)

        # Sort and search
        search = request.search
        if search:
            events = searchutils.event_keyword_chron_search(events, search)
        else:
            events = searchutils.event_chron_sort(events)

        return messages.EventCollection(items=events)

    @endpoints.method(messages.EVENT_PATCH_RESOURCE, messages.EventProperties,
                      http_method="PATCH", path="{event_id}")
    def patch(self, request):
        """
        Update an event's data.

        Only Event.hidden and Event.starred can be changed.  An event cannot be
        starred if it is hidden.

        :type request: messages.EVENT_PATCH_RESOURCE
        """
        user_id = authutils.require_user_id()

        # Get ndb key for calendar
        cal_id = request.calendar_id
        event_id = request.event_id
        user_key = models.get_user_key(user_id)
        cal_key = ndb.Key(models.Calendar, cal_id, parent=user_key)
        if cal_key.get() is None:
            raise endpoints.NotFoundException(
                "No calendar with id of \"{}\" in user's list.".format(cal_id))

        # Get or create model from calendar key and event id
        model = ndb.Key(models.Event, event_id, parent=cal_key).get()
        if model is None:
            model = models.Event(id=event_id, parent=cal_key)

        if request.recurrence_id is not None:
            recurring_parent_model = ndb.Key(
                models.Event, request.recurrence_id, parent=cal_key).get()
        else:
            recurring_parent_model = None

        # Set properties on the model from the request
        if recurring_parent_model is not None:
            model.hidden = recurring_parent_model.hidden
            model.starred = recurring_parent_model.starred
        if request.hidden is not None:
            model.hidden = request.hidden
        if request.starred is not None:
            model.starred = request.starred
        if model.hidden:
            model.starred = False

        model.put()
        return messages.EventProperties(
            event_id=event_id,
            calendar_id=cal_id,
            hidden=model.hidden,
            starred=model.starred
        )

    @endpoints.method(messages.EVENT_ID_RESOURCE, messages.EventProperties,
                      http_method="DELETE", path="{event_id}")
    def reset(self, request):
        """
        Remove data saved for an event.

        :type request: messages.EVENT_ID_RESOURCE
        """
        user_id = authutils.require_user_id()

        user_key = models.get_user_key(user_id)
        cal_key = ndb.Key(models.Calendar, request.calendar_id, parent=user_key)
        event_key = ndb.Key(models.Event, request.event_id, parent=cal_key)
        entity = event_key.get()
        event_key.delete()
        return messages.EventProperties(
            event_id=request.event_id,
            calendar_id=request.calendar_id,
            hidden=entity.hidden,
            starred=entity.starred
        )
