"""API for managing events."""

import logging

import endpoints
from google.appengine.ext import ndb
from protorpc import remote

from ticktockapi import ticktock_api
import messages
import models
import authutils
import gapiutils
import searchutils
import strings

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


@ticktock_api.api_class(resource_name="events",
                        path="calendars/{calendarId}/events",
                        auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class EventsAPI(remote.Service):
    """Manage events."""

    @endpoints.method(messages.EVENT_SEARCH_RESOURCE, messages.EventCollection,
                      http_method="GET", path="/calendars/{calendarId}/events")
    def list(self, request):
        """
        Get a list of events for a given calendar.

        :type request: messages.EVENT_SEARCH_RESOURCE
        """
        user_id = authutils.require_user_id()

        user_key = models.get_user_key(user_id)
        service = authutils.get_service(authutils.CALENDAR_API_NAME,
                                        authutils.CALENDAR_API_VERSION)

        # TODO: implement paging
        # get all the data for forever, then cache the extra in the datastore

        # TODO: add this after paging as part of said recursion
        # page_size = 10
        # events = []
        # while len(events) < page_size and next_page_token:

        # Get event list from the google api
        events = gapiutils.get_events(service, request.calendarId)

        # Update event list with fields stored in the datastore
        recurring_events = {}
        chosen_events = []
        cal_key = ndb.Key(models.Calendar, request.calendarId,
                          parent=user_key)
        if cal_key.get() is None:
            raise endpoints.NotFoundException()
        for event in events:
            event_key = ndb.Key(models.Event, event.eventId, parent=cal_key)
            event_entity = event_key.get()

            if event_entity is not None:
                event.hidden = event_entity.hidden
                event.starred = event_entity.starred

            recur_id = event.recurrenceId
            if recur_id is not None:
                saved = recur_id in recurring_events
                if saved:
                    recurrence_entity = recurring_events[recur_id]
                else:
                    recurrence_entity = ndb.Key(models.Event, recur_id,
                                                parent=cal_key).get()
                    recurring_events[recur_id] = recurrence_entity
                if recurrence_entity is not None:
                    if event.hidden is None:
                        event.hidden = recurrence_entity.hidden
                    if event.starred is None and recurrence_entity.starred:
                        # Only ever show one iteration of a starred recurring
                        # event, unless an individual iteration is starred
                        if saved:
                            # Essentially deletes the event, since it is not
                            # added to chosen_events.
                            continue
                        else:
                            event.starred = True

            if event.hidden is None:
                event.hidden = False
            if event.starred is None:
                event.starred = False

            if request.hidden is not None and event.hidden != request.hidden:
                # Essentially deletes the event, since it is not added to
                # chosen_events.
                continue

            chosen_events.append(event)

        events = chosen_events

        # TODO: if len(events) < page size: recurse and get part of next page

        # This will go before the other logic, and be cached.
        # Insert any starred events not included if hidden = False or None.
        if not request.hidden:
            starred = True
            starred_query = models.Event.query(models.Event.starred == starred,
                                               ancestor=cal_key)
            for starred_key in starred_query.iter(keys_only=True):
                entity_id = starred_key.string_id()
                for event in events:
                    if event.eventId == entity_id:
                        break
                else:
                    try:
                        event = gapiutils.get_event(
                            service, starred_key.parent().string_id(),
                            entity_id)
                        event.starred = True
                        event.hidden = False
                        events.append(event)
                    except endpoints.NotFoundException:
                        logging.info(strings.LOGGING_DELETE_UNBOUND_EVENT
                                     .format(user_id=user_id,
                                             calendar_id=request.calendarId,
                                             event_id=request.eventId))
                        starred_key.delete()
                    except gapiutils.OldEventError:
                        logging.info(strings.LOGGING_DELETE_OLD_EVENT
                                     .format(user_id=user_id,
                                             calendar_id=request.calendarId,
                                             event_id=request.eventId))
                        starred_key.delete()

        # Sort and search
        search = request.search
        if search:
            events = searchutils.event_keyword_chron_search(events, search)
        else:
            events = searchutils.event_chron_sort(events)

        return messages.EventCollection(items=events)

    @staticmethod
    def get_event_entity(user_id, calendar_id, event_id):
        """
        Retrieve or create an event entity from calendar and event ids.

        :type user_id: unicode
        :type calendar_id: str
        :type event_id: str
        :rtype: models.Event
        """
        # Get ndb key for calendar
        user_key = models.get_user_key(user_id)
        cal_key = ndb.Key(models.Calendar, calendar_id, parent=user_key)
        if cal_key.get() is None:
            raise endpoints.NotFoundException()

        # Get or create entity from calendar key and event id
        entity = ndb.Key(models.Event, event_id, parent=cal_key).get()
        if entity is None:
            entity = models.Event(id=event_id, parent=cal_key)
        return entity

    @endpoints.method(messages.EVENT_ID_RESOURCE, messages.EventProperties,
                      http_method="GET", path="{eventId}")
    def get(self, request):
        """
        Get an individual event's data.

        :type request: messages.CALENDAR_ID_RESOURCE
        """
        user_id = authutils.require_user_id()

        service = authutils.get_service(authutils.CALENDAR_API_NAME,
                                        authutils.CALENDAR_API_VERSION)
        event = gapiutils.get_event(service, request.calendarId,
                                    request.eventId)

        user_key = models.get_user_key(user_id)
        cal_key = ndb.Key(models.Calendar, request.calendarId, parent=user_key)
        if cal_key.get() is None:
            raise endpoints.NotFoundException()
        entity = ndb.Key(models.Event, request.eventId, parent=cal_key).get()

        if entity is not None:
            event.hidden = entity.hidden
            event.starred = entity.starred

        if event.hidden is None:
            event.hidden = False
        if event.starred is None:
            event.starred = False

        return event

    @endpoints.method(messages.EVENT_WRITE_RESOURCE,
                      messages.EventWriteProperties,
                      http_method="PATCH", path="{eventId}")
    def patch(self, request):
        """
        Update an event's data.

        An event cannot be starred if it is hidden, and hiding a starred event
        unstars it.

        :type request: messages.EVENT_WRITE_RESOURCE
        """
        user_id = authutils.require_user_id()

        entity = self.get_event_entity(user_id, request.calendarId,
                                       request.eventId)

        # Set properties on the entity from the request
        if request.hidden is not None:
            entity.hidden = request.hidden
        if request.starred is not None:
            entity.starred = request.starred
        if entity.hidden:
            entity.starred = False

        entity.put()
        return messages.EventWriteProperties(
                hidden=entity.hidden,
                starred=entity.starred)

    @endpoints.method(messages.EVENT_WRITE_RESOURCE,
                      messages.EventWriteProperties,
                      http_method="PUT", path="{eventId}")
    def put(self, request):
        """
        Set an event's data.

        An event cannot be starred if it is hidden.  If both are set to true,
        hidden will win.

        :type request: messages.EVENT_WRITE_RESOURCE
        """
        user_id = authutils.require_user_id()

        entity = self.get_event_entity(user_id, request.calendarId,
                                       request.eventId)

        # Set properties on the entity from the request, or if the request is
        # null, delete the entity.
        if request.hidden is None and request.starred is None:
            entity.key.delete()
            return messages.EventWriteProperties()
        else:
            entity.hidden = request.hidden
            entity.starred = request.starred
            if entity.hidden:
                entity.starred = False

            entity.put()
            return messages.EventWriteProperties(
                    hidden=entity.hidden,
                    starred=entity.starred)
