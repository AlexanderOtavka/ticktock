"""Tools for getting data from the Google Calendar API, once a service has been generated."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

import logging
from datetime import datetime

import messages

API_NAME = "calendar"
API_VERSION = "v3"

CALENDAR_FIELDS = "id,summary,backgroundColor"
EVENT_FIELDS = "id,summary,start,end"
LIST_FIELDS = "nextPageToken,items({})"


class OldEventError(Exception):
    pass


def get_personal_calendars(service):
    page_token = None
    calendars = []
    while True:
        api_query_result = service.calendarList().list(fields=LIST_FIELDS.format(CALENDAR_FIELDS),
                                                       pageToken=page_token).execute()
        logging.debug("query result = " + str(api_query_result))
        calendars += [
            messages.Calendar(
                calendar_id=item["id"],
                name=item["summary"],
                color=item["backgroundColor"],
                hidden=False,
            )
            for item in api_query_result["items"]
            ]
        page_token = api_query_result.get("nextPageToken")
        if not page_token:
            break
    return calendars


def get_public_calendars():
    return []


def datetime_from_string(string):
    date_format = "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(string[:19], date_format)


def datetime_from_date_string(string):
    date_format = "%Y-%m-%d"
    return datetime.strptime(string[:10], date_format)


def get_events(service, cal_id, page_token=None, time_zone="UTC"):
    events = []
    now = datetime.utcnow().isoformat() + "Z"
    result = service.events().list(
        fields=LIST_FIELDS.format(EVENT_FIELDS),
        calendarId=cal_id,
        pageToken=page_token,
        maxResults=10,
        timeMin=now,
        timeZone=time_zone,
    ).execute()

    for item in result["items"]:
        name = "(Untitled Event)"
        if "summary" in item:
            name = item["summary"]

        start = item["start"]
        if "dateTime" in start:
            start_date = datetime_from_string(start["dateTime"])
        else:
            start_date = datetime_from_date_string(start["date"])

        end = item["end"]
        if "dateTime" in end:
            end_date = datetime_from_string(end["dateTime"])
        else:
            end_date = datetime_from_date_string(end["date"])

        event = messages.Event(
            event_id=item["id"],
            calendar_id=cal_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            hidden=False,
            starred=False,
        )
        events.append(event)

    return events


def get_event(service, cal_id, event_id, time_zone="UTC"):
    """Get a specific event by ID.

    Raises:
        OldEventError: if the requested event takes place in the past.
    """
    result = service.events().get(
        fields=EVENT_FIELDS,
        calendarId=cal_id,
        eventId=event_id,
        timeZone=time_zone,
    ).execute()
    now = datetime.utcnow()
    end_date = datetime_from_string(result["end"]["dateTime"])
    if end_date < now:
        raise OldEventError("Event \"{}\" ended in the past.".format(event_id))

    return messages.Event(
        event_id=event_id,
        calendar_id=cal_id,
        name=result["summary"],
        start_date=datetime_from_string(result["start"]["dateTime"]),
        end_date=end_date,
        hidden=False,
        starred=False,
    )
