"""API for managing events."""

import logging

import endpoints
from google.appengine.ext import ndb
from protorpc import remote
import basehash

from ticktockapi import ticktock_api
import messages
import models
import authutils
import gapiutils
import searchutils
import strings

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


BASE58 = basehash.base58()


@ticktock_api.api_class(resource_name="events",
                        path="calendars/{calendarId}/events",
                        auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class EventsAPI(remote.Service):
    """Manage events."""

    @staticmethod
    def get_starred(calendar_key, service, time_zone):
        """
        Get an array of all starred events in given calendar and the ids.

        :type calendar_key: ndb.Key
        :param service: Calendar resource object.
        :type time_zone: str
        :rtype: (list[messages.EventProperties], list[str])
        """
        events = []
        ids = []
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
                ids.append(starred_key.string_id())
            except endpoints.NotFoundException:
                logging.info(strings.logging_delete_unbound_event(
                        user_id=user_id, calendar_id=calendar_id,
                        event_id=starred_key.string_id()))
                starred_key.delete()
            except gapiutils.OldEventError:
                pass
        return events, ids

    @staticmethod
    def filter_and_update_events(unfiltered_events, starred_event_ids,
                                 calendar_key, request_hidden):
        """
        Update and prune event list with fields stored in the datastore.

        :type unfiltered_events: list[messages.EventProperties]
        :type starred_event_ids: list[str]
        :type calendar_key: ndb.Key
        :type request_hidden: bool
        :rtype: list[messages.EventProperties]
        """
        chosen = []
        for event in unfiltered_events:
            for starred_event_id in starred_event_ids:
                if (starred_event_id == event.eventId or
                        starred_event_id == event.recurrenceId):
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

    @staticmethod
    def sort_and_search(events, search):
        if search:
            return searchutils.event_keyword_chron_search(events, search)
        else:
            return searchutils.event_chron_sort(events)

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

        if not request.timeZone:
            request.timeZone = gapiutils.get_calendar_time_zone(
                    service, request.calendarId)
        if request.pageToken:
            request.pageToken = BASE58.decode(request.pageToken)

        starred_events = []
        """:type: list[messages.EventProperties]"""

        cached_events = []
        """:type: list[messages.EventProperties]"""

        starred_event_ids = []
        """:type: list[str]"""

        calendar_key = ndb.Key(models.Calendar, request.calendarId,
                               parent=user_key)
        if calendar_key.get() is None:
            raise endpoints.NotFoundException(
                    strings.error_calendar_not_added(
                            calendar_id=request.calendarId))

        if request.pageToken:
            # Grab the cache for given page token
            cache = ndb.Key(models.EventCacheGroup, request.pageToken,
                            parent=user_key).get()
            """:type: models.EventCacheGroup"""

            if (cache is None or cache.sequence_hash !=
                    models.EventCacheGroup.get_sequence_hash(request)):
                raise endpoints.BadRequestException(
                        strings.ERROR_INVALID_VALUE)

            gapi_next_page_token = cache.next_page_token
            for event_model in cache.items:
                cached_events.append(event_model.to_message(request.timeZone))
        else:
            gapi_next_page_token = None

            # Insert any starred events not included if hidden = False or None.
            if not request.hidden:
                starred_events, starred_event_ids = self.get_starred(
                        calendar_key, service, request.timeZone)

        if len(starred_event_ids) > request.maxResults:
            starred_event_ids, extra_starred_ids = (
                    starred_event_ids[:request.maxResults],
                    starred_event_ids[request.maxResults:])
        else:
            extra_starred_ids = []

        # Initial sort and search, before checking the length
        events = self.sort_and_search(starred_events, request.search)
        """:type: list[messages.EventProperties]"""

        events += cached_events

        # TODO: make this a for loop to 10, and last add search/sort to it
        if len(events) < request.maxResults:
            # Get event list from the google api
            api_events, gapi_next_page_token = gapiutils.get_events(
                    service, request.calendarId, request.timeZone,
                    gapi_next_page_token, request.maxResults)

            events += self.filter_and_update_events(
                    api_events, starred_event_ids, calendar_key, request.hidden)

        # Sort and search again after adding api events
        events = self.sort_and_search(events, request.search)
        # TODO: if gapi_next_page_token is None: break

        if len(events) >= request.maxResults:
            # Save extra for later
            events, extra = (events[:request.maxResults],
                             events[request.maxResults:])

            # Make a new cache object
            new_cache = models.EventCacheGroup(
                next_page_token=gapi_next_page_token,
                extra_starred_ids=extra_starred_ids,
                parent=user_key
            )
            assert new_cache.items == []
            for extra_event in extra:
                new_cache.items.append(
                        models.EventCache.from_message(extra_event))
            new_cache.generate_hashes(request)

            # Check for duplicates, save new_cache if not
            query = models.EventCacheGroup.query(
                models.EventCacheGroup.unique_hash == new_cache.unique_hash,
                ancestor=user_key
            )
            assert len(query.fetch()) <= 1
            for key in query.iter(keys_only=True):
                cache_key = key
                break
            else:
                cache_key = None
            if cache_key is None:
                cache_key = new_cache.put()
            next_page_token = BASE58.encode(cache_key.integer_id())
        else:
            next_page_token = None

        return messages.EventCollection(
            items=events,
            nextPageToken=next_page_token
        )

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
        event = gapiutils.get_event(service, request.calendarId,
                                    request.eventId, request.timeZone)

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
        gapiutils.get_event(service, calendar_id, event_id, "UTC",
                            validation_only=True)

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
