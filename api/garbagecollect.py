"""Clear out old or unbound datastore entities."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

import logging
import httplib
from datetime import datetime

import webapp2
from apiclient.errors import HttpError
import gapiutils
import authutils
import models


class GarbageCollector(webapp2.RequestHandler):
    """Respond to scheduled chron job by ensuring the event database is clean."""

    # noinspection PyMethodMayBeStatic
    def get(self):
        credentials_entity_list = authutils.CredentialsModel.all()
        for cred_entity in credentials_entity_list:
            service = authutils.get_service_from_credentials(
                gapiutils.API_NAME, gapiutils.API_VERSION, cred_entity.credentials)
            user_id = cred_entity.key().name()
            events = models.Event.query(ancestor=models.get_user_key(user_id)).fetch()
            for event in events:
                event_id = event.key.string_id()
                cal_id = event.key.parent().string_id()
                api_object = None
                try:
                    api_object = service.events().get(calendarId=cal_id, eventId=event_id,
                                                      timeZone="UTC", fields="end").execute()
                except HttpError as e:
                    if e.resp.status == httplib.NOT_FOUND:
                        logging.info(
                            "Deleted: unbound Event entity with event_id = \"{}\" and " +
                            "cal_id = \"{}\" and user_id = \"{}\".".format(event_id, cal_id, user_id))
                        event.key.delete()
                now = datetime.utcnow()
                end = api_object["end"]
                event_end = gapiutils.datetime_from_date_string(end["date"])
                if "dateTime" in end:
                    event_end = gapiutils.datetime_from_string(end["dateTime"])
                if event_end < now:
                    logging.info(
                        "Deleted: old Event entity with event_id = \"{}\" and cal_id = \"{}\" and " +
                        "user_id = \"{}\".".format(event_id, cal_id, user_id))
                    event.key.delete()


collectors = webapp2.WSGIApplication([
    ("/_ah/garbagecollect/go", GarbageCollector),
])
