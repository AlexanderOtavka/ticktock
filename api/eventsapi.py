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

    @staticmethod
    def get_starred(calendar_key, service, time_zone):
        """
        Get an array of all starred events in given calendar.

        :type calendar_key: ndb.Key
        :param service: Calendar resource object.
        :type time_zone: str
        :rtype: list[messages.EventProperties]
        """
        events = []
        user_id = calendar_key.parent().string_id()
        calendar_id = calendar_key.string_id()
        starred = True
        starred_query = models.Event.query(models.Event.starred == starred,
                                           ancestor=calendar_key)
        for starred_key in starred_query.iter(keys_only=True):
            try:
                event = gapiutils.get_event(service, calendar_id,
                                            starred_key.string_id(), time_zone)
                event.starred = True
                event.hidden = False
                events.append(event)
            except endpoints.NotFoundException:
                logging.info(strings.logging_delete_unbound_event(
                        user_id=user_id, calendar_id=calendar_id,
                        event_id=starred_key.string_id()))
                starred_key.delete()
            except gapiutils.OldEventError:
                logging.info(strings.logging_delete_old_event(
                        user_id=user_id, calendar_id=calendar_id,
                        event_id=starred_key.string_id()))
                starred_key.delete()
        return events

    @staticmethod
    def filter_and_update_events(unfiltered_events, starred_events,
                                 calendar_key, request_hidden):
        """
        Update and prune event list with fields stored in the datastore.

        :type unfiltered_events: list[messages.EventProperties]
        :type starred_events: list[messages.EventProperties]
        :type calendar_key: ndb.Key
        :type request_hidden: bool
        :rtype: list[messages.EventProperties]
        """
        chosen = []
        for event in unfiltered_events:
            for starred_event in starred_events:
                if (starred_event.eventId == event.eventId or
                        starred_event.eventId == event.recurrenceId):
                    event.starred = True
                    break
            else:
                event.starred = False

            if event.starred:
                # Essentially deletes the event, since it is not added to
                # chosen.
                continue

            entity = ndb.Key(models.Event, event.eventId,
                             parent=calendar_key).get()

            if entity is not None:
                event.hidden = entity.hidden

            if event.hidden is None and event.recurrenceId is not None:
                recurrence_entity = ndb.Key(models.Event, event.recurrenceId,
                                            parent=calendar_key).get()
                if recurrence_entity is not None:
                    event.hidden = recurrence_entity.hidden

            if event.hidden is None:
                event.hidden = False

            if request_hidden is not None and event.hidden != request_hidden:
                # Essentially deletes the event, since it is not added to
                # chosen.
                continue

            chosen.append(event)
        return chosen

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

        events = []

        calendar_key = ndb.Key(models.Calendar, request.calendarId,
                               parent=user_key)
        if calendar_key.get() is None:
            raise endpoints.NotFoundException(
                    strings.error_calendar_not_added(
                            calendar_id=request.calendarId))

        # Insert any starred events not included if hidden = False or None.
        if not request.hidden:
            starred_events = self.get_starred(calendar_key, service,
                                              request.timeZone)
            events += starred_events
        else:
            starred_events = []

        page_size = 10
        # TODO: add this after paging as part of said recursion
        # next_page_token = request.pageToken
        # while len(events) < page_size and next_page_token:
        if len(events) < page_size:
            # Get event list from the google api
            api_events = gapiutils.get_events(service, request.calendarId,
                                              request.timeZone,
                                              request.pageToken, page_size)

            events += self.filter_and_update_events(
                    api_events, starred_events, calendar_key, request.hidden)

        # Sort and search
        search = request.search
        if search:
            events = searchutils.event_keyword_chron_search(events, search)
        else:
            events = searchutils.event_chron_sort(events)

        return messages.EventCollection(items=events)

    @endpoints.method(messages.EVENT_ID_RESOURCE, messages.EventProperties,
                      http_method="GET", path="{eventId}")
    def get(self, request):
        """
        Get an individual event's data.

        :type request: messages.EVENT_ID_RESOURCE
        """
        user_id = authutils.require_user_id()

        service = authutils.get_service(authutils.CALENDAR_API_NAME,
                                        authutils.CALENDAR_API_VERSION)
        try:
            event = gapiutils.get_event(service, request.calendarId,
                                        request.eventId, request.timeZone)
        except gapiutils.OldEventError:
            raise endpoints.ForbiddenException(
                    strings.error_old_event(event_id=request.eventId))

        user_key = models.get_user_key(user_id)
        cal_key = ndb.Key(models.Calendar, request.calendarId, parent=user_key)
        if cal_key.get() is None:
            raise endpoints.NotFoundException(
                    strings.error_calendar_not_added(
                            calendar_id=request.calendarId))
        entity = ndb.Key(models.Event, request.eventId, parent=cal_key).get()

        if entity is not None:
            event.hidden = entity.hidden
            event.starred = entity.starred

        if event.hidden is None:
            event.hidden = False
        if event.starred is None:
            event.starred = False

        return event

    @staticmethod
    def get_event_entity(user_id, calendar_id, event_id):
        """
        Retrieve or create an event entity from calendar and event ids.

        :type user_id: unicode
        :type calendar_id: str
        :type event_id: str
        :rtype: models.Event
        """
        # Validate event's existence
        service = authutils.get_service(authutils.CALENDAR_API_NAME,
                                        authutils.CALENDAR_API_VERSION)
        try:
            gapiutils.get_event(service, calendar_id, event_id, "UTC",
                                validation_only=True)
        except gapiutils.OldEventError:
            raise endpoints.ForbiddenException(
                    strings.error_old_event(event_id=event_id))

        # Get ndb key for calendar
        user_key = models.get_user_key(user_id)
        cal_key = ndb.Key(models.Calendar, calendar_id, parent=user_key)
        if cal_key.get() is None:
            raise endpoints.NotFoundException(
                    strings.error_calendar_not_added(calendar_id=calendar_id))

        # Get or create entity from calendar key and event id
        entity = ndb.Key(models.Event, event_id, parent=cal_key).get()
        if entity is None:
            entity = models.Event(id=event_id, parent=cal_key)
        return entity

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
