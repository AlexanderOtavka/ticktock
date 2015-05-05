'''Get data from the Google Calendar API, once a service has been generated.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


import logging
from datetime import datetime

import messages
import models


API_NAME = 'calendar'
API_VERSION = 'v3'


# TODO: optimize api requests to only ask for needed fields.

def get_personal_calendars(service):
    page_token = None
    calendars = []
    while True:
        api_query_result = service.calendarList().list(pageToken=page_token).execute()
        calendars += [
            messages.Calendar(
                calendar_id=item['id'],
                name=item['summary'],
                color=item['backgroundColor'],
                hidden=False,
            )
            for item in api_query_result['items']
        ]
        page_token = api_query_result.get('nextPageToken')
        if not page_token:
            break
    return calendars

def get_public_calendars():
    return []

def datetime_from_string(string):
    date_format = '%Y-%m-%dT%H:%M:%S'
    return datetime.strptime(string[:19], date_format)

def get_events(service, cal_id, page_token=None, time_zone=None):
    events = []
#    now = datetime.utcnow().isoformat() + 'Z'
    api_query_result = service.events().list(calendarId=cal_id, pageToken=page_token,
                                             maxResults=10, #timeMin=now,
                                             timeZone=time_zone).execute()

    for item in api_query_result['items']:
        try:
#            logging.debug('start = ' + str(item['start']['dateTime'][:-6]))
            event = messages.Event(
                event_id=item['id'],
                calendar_id=cal_id,
                name=item['summary'],
                start_date=datetime_from_string(item['start']['dateTime']),
                end_date=datetime_from_string(item['end']['dateTime']),
                hidden=False,
                starred=False,
            )
        except KeyError:
            continue
        events.append(event)

    return events
