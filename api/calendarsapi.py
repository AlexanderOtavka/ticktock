"""API for managing calendars."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

import logging

import endpoints
from google.appengine.ext import ndb
from protorpc import remote, message_types

from ticktockapi import ticktock_api
import messages
import models
import authutils
import gapiutils


@ticktock_api.api_class(resource_name="calendars", path="calendars",
                        auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class CalendarsAPI(remote.Service):
    """Manage user calendars added to ticktock."""

    @endpoints.method(message_types.VoidMessage, messages.CalendarCollection,
                      name="list", http_method="GET", path="/calendars")
    def list_calendars(self, request):
        """Get a list of calendars the user has chosen."""
        user_id = authutils.require_id()

        service = authutils.get_service(gapiutils.CALENDAR_API_NAME,
                                        gapiutils.CALENDAR_API_VERSION)
        all_calendars = (gapiutils.get_personal_calendars(service) +
                         gapiutils.get_public_calendars())

        user_key = models.get_user_key(user_id)
        chosen_ndb = models.Calendar.query(ancestor=user_key).fetch()
        chosen_calendars = []
        for entity in chosen_ndb:
            for cal in all_calendars:
                if cal.calendar_id == entity.key.string_id():
                    cal.hidden = entity.hidden
                    chosen_calendars.append(cal)
                    break
            else:
                logging.info(
                    "Deleted: unbound Calendar entity with calendar_id = " +
                    "\"{}\" and user_id = \"{}\"."
                    .format(entity.key.string_id(), user_id))
                entity.key.delete()

        return messages.CalendarCollection(items=chosen_calendars)

    @endpoints.method(messages.CalendarProperties, message_types.VoidMessage,
                      name="insert", http_method="POST", path="/calendars")
    def insert_calendar(self, request):
        """Add a calendar to the user's list."""
        user_id = authutils.require_id()

        cal_id = request.calendar_id
        user_key = models.get_user_key(user_id)
        model = models.Calendar(id=cal_id, parent=user_key)
        model.put()
        return message_types.VoidMessage()

    @endpoints.method(messages.CALENDAR_RESOURCE_CONTAINER,
                      messages.CalendarProperties,
                      name="patch", http_method="PATCH", path="{calendar_id}")
    def patch_calendar(self, request):
        """
        Update a calendar's data.

        Only Calendar.hidden can be changed.
        """
        user_id = authutils.require_id()

        cal_id = request.calendar_id
        user_key = models.get_user_key(user_id)
        model = ndb.Key(models.Calendar, cal_id, parent=user_key).get()
        if model is None:
            raise endpoints.NotFoundException(
                "No calendar with id of \"{}\" in user's list.".format(cal_id))

        temp = request.hidden
        if temp is not None:
            model.hidden = temp
        model.put()
        return messages.CalendarProperties(
            calendar_id=cal_id,
            hidden=model.hidden,
        )

    @endpoints.method(messages.CALENDAR_RESOURCE_CONTAINER,
                      messages.CalendarProperties,
                      name="delete", http_method="DELETE", path="{calendar_id}")
    def delete_calendar(self, request):
        """Remove a calendar from a user's list."""
        user_id = authutils.require_id()

        cal_id = request.calendar_id
        user_key = models.get_user_key(user_id)
        key = ndb.Key(models.Calendar, cal_id, parent=user_key)
        entity = key.get()
        key.delete()
        return messages.CalendarProperties(
            calendar_id=cal_id,
            hidden=entity.hidden,
        )
