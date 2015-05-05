'''Clear out old or unbound datastore entities.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


import logging
import httplib

import webapp2
#from google.appengine.ext import ndb
from apiclient.errors import HttpError

import calendar_api
import auth
import models


class GarbageCollector(webapp2.RequestHandler):
    def get(self):
        credentials_entity_list = auth.CredentialsModel.all()
        for cred_entity in credentials_entity_list:
            service = auth.get_service_from_credentials(
                calendar_api.API_NAME, calendar_api.API_VERSION, cred_entity.credentials)
            user_id = int(cred_entity.key().name())
            logging.debug('user_id = ' + repr(user_id))
            events = models.Event.query(ancestor=models.get_user_key(user_id)).fetch()
            for event in events:
                event_id = event.key.string_id()
                cal_id = event.key.parent().string_id()
                try:
                    api_object = service.events().get(calendarId=cal_id, eventId=event_id).execute()
                except HttpError as e:
                    if e.resp.status == httplib.NOT_FOUND:
                        logging.info(
                            'Unbound Event entity with event_id = "{}" and cal_id = "{}" and \
                            user_id = {} deleted.'.format(event_id, cal_id, user_id))
                        event.key.delete()
                logging.debug('api_object = ' + str(api_object))
                # TODO: delete old events.

collectors = webapp2.WSGIApplication([
    ('/_ah/garbagecollect/go', GarbageCollector),
])
