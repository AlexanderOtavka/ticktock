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
            AppAssertionCredentials(authutils.SERVICE_ACCOUNT_SCOPES)
        )
        all_calendars = (gapiutils.get_calendars(user_service) +
                         gapiutils.get_calendars(app_service))

        # Filter out calendars not added in user's ndb
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

        # Sort and search
        search = request.search
        if search:
            chosen_calendars = searchutils.calendar_keyword_alpha_search(
                chosen_calendars, search)
        else:
            chosen_calendars = searchutils.calendar_alpha_sort(chosen_calendars)

        return messages.CalendarCollection(items=chosen_calendars)

    @endpoints.method(messages.CALENDAR_ID_RESOURCE, message_types.VoidMessage,
                      http_method="POST", path="/calendars")
    def insert(self, request):
        """
        Add a calendar to the user's list.

        :type request: messages.CALENDAR_ID_RESOURCE
        """
        user_id = authutils.require_user_id()

        cal_id = request.calendar_id
        user_key = models.get_user_key(user_id)
        model = models.Calendar(id=cal_id, parent=user_key)
        model.put()
        return message_types.VoidMessage()

    @endpoints.method(messages.CALENDAR_PATCH_RESOURCE,
                      messages.CalendarProperties,
                      http_method="PATCH", path="{calendar_id}")
    def patch(self, request):
        """
        Update a calendar's data.

        Only Calendar.hidden can be changed.

        :type request: messages.CALENDAR_PATCH_RESOURCE
        """
        user_id = authutils.require_user_id()

        # Get the ndb model
        cal_id = request.calendar_id
        user_key = models.get_user_key(user_id)
        model = ndb.Key(models.Calendar, cal_id, parent=user_key).get()
        if model is None:
            raise endpoints.NotFoundException(
                "No calendar with id of \"{}\" in user's list.".format(cal_id))

        # Set properties from request on the model
        hidden = request.hidden
        if hidden is not None:
            model.hidden = hidden

        model.put()
        return messages.CalendarProperties(
            calendar_id=cal_id,
            hidden=model.hidden,
        )

    @endpoints.method(messages.CALENDAR_ID_RESOURCE,
                      messages.CalendarProperties,
                      http_method="DELETE", path="{calendar_id}")
    def delete(self, request):
        """
        Remove a calendar from a user's list.

        :type request: messages.CALENDAR_ID_RESOURCE
        """
        user_id = authutils.require_user_id()

        cal_id = request.calendar_id
        user_key = models.get_user_key(user_id)
        key = ndb.Key(models.Calendar, cal_id, parent=user_key)
        entity = key.get()
        key.delete()
        return messages.CalendarProperties(
            calendar_id=cal_id,
            hidden=entity.hidden,
        )
