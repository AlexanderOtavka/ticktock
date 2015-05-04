'''Get data from the Google Calendar API, once a service has been generated.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


import logging
from datetime import datetime

import messages
import models


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

def get_events(service, cal_id, page_token=None, time_zone=None):
    events = []
    now = datetime.utcnow().isoformat() + 'Z'
    api_query_result = service.events().list(calendarId=cal_id, pageToken=page_token,
                                             maxResults=10, timeMin=now,
                                             timeZone=time_zone).execute()
    date_format = '%Y-%m-%dT%H:%M:%S'

    for item in api_query_result['items']:
        try:
#            logging.debug('start = ' + str(item['start']['dateTime'][:-6]))
            event = messages.Event(
                event_id=item['id'],
                calendar_id=cal_id,
                name=item['summary'],
                start_date=datetime.strptime(item['start']['dateTime'][:-6], date_format),
                end_date=datetime.strptime(item['end']['dateTime'][:-6], date_format),
                hidden=False,
                starred=False,
            )
        except KeyError:
            continue
        events.append(event)

    return events
