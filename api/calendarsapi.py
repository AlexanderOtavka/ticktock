"""API for managing calendars."""

import logging

import endpoints
from google.appengine.ext import ndb
from protorpc import remote, message_types
from oauth2client.appengine import AppAssertionCredentials

from ticktockapi import ticktock_api
import messages
import models
import authutils
import gapiutils
import searchutils
import strings

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


@ticktock_api.api_class(resource_name="calendars", path="calendars",
                        auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class CalendarsAPI(remote.Service):
    """Manage user calendars added to ticktock."""

    @endpoints.method(messages.CALENDAR_SEARCH_RESOURCE,
                      messages.CalendarCollection,
                      http_method="GET", path="/calendars")
    def list(self, request):
        """
        Get a list of calendars the user has chosen.

        :type request: messages.CALENDAR_SEARCH_RESOURCE
        """
        user_id = authutils.require_user_id()

        # Get list of all calendars available to the user
        user_service = authutils.get_service(authutils.CALENDAR_API_NAME,
                                             authutils.CALENDAR_API_VERSION)
        app_service = authutils.get_service(
                authutils.CALENDAR_API_NAME,
                authutils.CALENDAR_API_VERSION,
                AppAssertionCredentials(authutils.SERVICE_ACCOUNT_SCOPES))
        all_calendars = (gapiutils.get_calendars(user_service) +
                         gapiutils.get_calendars(app_service))

        # Filter out calendars not added in user's ndb
        user_key = models.get_user_key(user_id)
        chosen_ndb = models.Calendar.query(ancestor=user_key)
        if request.hidden is not None:
            chosen_ndb.filter(models.Calendar.hidden == request.hidden)
        chosen_calendars = []
        for entity in chosen_ndb.fetch():
            for cal in all_calendars:
                if cal.calendarId == entity.key.string_id():
                    cal.hidden = entity.hidden
                    if cal.hidden is None:
                        cal.hidden = False
                    chosen_calendars.append(cal)
                    break
            else:
                logging.info(strings.LOGGING_DELETE_UNBOUND_CALENDAR
                             .format(calendar_id=entity.key.string_id(),
                                     user_id=user_id))
                entity.key.delete()

        # Sort and search
        search = request.search
        if search:
            chosen_calendars = searchutils.calendar_keyword_alpha_search(
                chosen_calendars, search)
        else:
            chosen_calendars = searchutils.calendar_alpha_sort(chosen_calendars)

        return messages.CalendarCollection(items=chosen_calendars)

    @staticmethod
    def get_calendar_entity(user_id, calendar_id):
        """
        Retrieve or create a calendar entity from a calendar id.

        :type user_id: unicode
        :type calendar_id: str
        :rtype: models.Calendar
        """
        # Get the ndb entity
        user_key = models.get_user_key(user_id)
        entity = ndb.Key(models.Calendar, calendar_id,
                         parent=user_key).get()
        if entity is None:
            entity = models.Calendar(id=calendar_id, parent=user_key)
        return entity

    @endpoints.method(messages.CALENDAR_ID_RESOURCE,
                      messages.CalendarProperties,
                      http_method="GET", path="{calendarId}")
    def get(self, request):
        """
        Get an individual calendar's data.

        :type request: messages.CALENDAR_ID_RESOURCE
        """
        user_id = authutils.require_user_id()

        service = authutils.get_service(authutils.CALENDAR_API_NAME,
                                        authutils.CALENDAR_API_VERSION)
        calendar = gapiutils.get_calendar(service, request.calendarId)

        user_key = models.get_user_key(user_id)
        entity = ndb.Key(models.Calendar, request.calendarId,
                         parent=user_key).get()
        if entity is None:
            raise endpoints.NotFoundException()

        calendar.hidden = entity.hidden
        if calendar.hidden is None:
            calendar.hidden = False

        return calendar

    @endpoints.method(messages.CALENDAR_WRITE_RESOURCE,
                      messages.CalendarWriteProperties,
                      http_method="PATCH", path="{calendarId}")
    def patch(self, request):
        """
        Update a calendar's data.

        :type request: messages.CALENDAR_WRITE_RESOURCE
        """
        user_id = authutils.require_user_id()

        entity = self.get_calendar_entity(user_id, request.calendarId)

        # Set properties from request on the entity
        if request.hidden is not None:
            entity.hidden = request.hidden

        entity.put()
        return messages.CalendarWriteProperties(hidden=entity.hidden)

    @endpoints.method(messages.CALENDAR_WRITE_RESOURCE,
                      messages.CalendarWriteProperties,
                      http_method="PUT", path="{calendarId}")
    def put(self, request):
        """
        Set a calendar's data, or create a calendar from data.

        :type request: messages.CALENDAR_WRITE_RESOURCE
        """
        user_id = authutils.require_user_id()

        entity = self.get_calendar_entity(user_id, request.calendarId)

        # Set properties from request on the entity
        entity.hidden = request.hidden

        entity.put()
        return messages.CalendarWriteProperties(hidden=entity.hidden)

    @endpoints.method(messages.CALENDAR_ID_RESOURCE, message_types.VoidMessage,
                      http_method="DELETE", path="{calendarId}")
    def delete(self, request):
        """
        Remove a calendar from a user's list.

        :type request: messages.CALENDAR_ID_RESOURCE
        """
        user_id = authutils.require_user_id()

        user_key = models.get_user_key(user_id)
        key = ndb.Key(models.Calendar, request.calendarId, parent=user_key)
        if key.get() is None:
            raise endpoints.NotFoundException()
        key.delete()

        # Does not delete the calendar's events' data, just in case the user
        # wants to undo, they can re-add the calendar, and have all of their
        # starred and hidden events remain.  I'm still not sure if that's the
        # best behavior, but I'm going to err on the side of least destruction.

        return message_types.VoidMessage()
