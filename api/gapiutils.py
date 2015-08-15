"""Tools for getting data from the Google Calendar API."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

from datetime import datetime

from endpoints import NotFoundException, ForbiddenException
from apiclient.errors import HttpError

import messages

CALENDAR_API_NAME = "calendar"
CALENDAR_API_VERSION = "v3"

CALENDAR_FIELDS = "id,summary,backgroundColor"
EVENT_FIELDS = "id,summary,start,end"
LIST_FIELDS = "nextPageToken,items({})"


class OldEventError(Exception):
    pass


def get_calendars(service):
    """
    Return a list of the current user's calendars.

    :rtype: list[messages.CalendarProperties]
    :raise ForbiddenException: API request failed with status 403.
    :raise NotFoundException: API request failed with status 404.
   """
    page_token = None
    calendars = []

    while True:
        try:
            api_query_result = service.calendarList().list(
                fields=LIST_FIELDS.format(CALENDAR_FIELDS),
                pageToken=page_token
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise NotFoundException()
            elif e.resp.status == 403:
                raise ForbiddenException()
            else:
                raise

        calendars += [
            messages.CalendarProperties(
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


def datetime_from_string(string):
    """
    Parse a datetime string.

    :type string: str
    :rtype: datetime
    """
    date_format = "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(string[:19], date_format)


def datetime_from_date_string(string):
    """
    Parse a date string.

    :type string: str
    :rtype: datetime
    """
    date_format = "%Y-%m-%d"
    return datetime.strptime(string[:10], date_format)


def get_events(service, cal_id, page_token=None, time_zone="UTC"):
    """
    Return a list of events for a given calendar.

    :type cal_id: str
    :type page_token: str
    :type time_zone: str
    :rtype: list[messages.EventProperties]
    :raise ForbiddenException: API request failed with status 403.
    :raise NotFoundException: API request failed with status 404.
    """
    events = []
    now = datetime.utcnow().isoformat() + "Z"
    try:
        result = service.events().list(
            fields=LIST_FIELDS.format(EVENT_FIELDS),
            calendarId=cal_id,
            pageToken=page_token,
            maxResults=10,
            timeMin=now,
            timeZone=time_zone,
        ).execute()
    except HttpError as e:
        if e.resp.status == 404:
            raise NotFoundException()
        elif e.resp.status == 403:
            raise ForbiddenException()
        else:
            raise

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

        event = messages.EventProperties(
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
    """
    Get a specific event by ID.

    :type cal_id: str
    :type event_id: str
    :type time_zone: str
    :rtype: messages.EventProperties
    :raise OldEventError: The requested event takes place in the past.
    :raise ForbiddenException: API request failed with status 403.
    :raise NotFoundException: API request failed with status 404.
    """
    try:
        result = service.events().get(
            fields=EVENT_FIELDS,
            calendarId=cal_id,
            eventId=event_id,
            timeZone=time_zone,
        ).execute()
    except HttpError as e:
        if e.resp.status == 404:
            raise NotFoundException()
        elif e.resp.status == 403:
            raise ForbiddenException()
        else:
            raise

    start = result["start"]
    if "dateTime" in start:
        start_date = datetime_from_string(start["dateTime"])
    else:
        start_date = datetime_from_date_string(start["date"])

    end = result["end"]
    if "dateTime" in end:
        end_date = datetime_from_string(end["dateTime"])
    else:
        end_date = datetime_from_date_string(end["date"])

    now = datetime.utcnow()
    if end_date < now:
        raise OldEventError("Event \"{}\" ended in the past.".format(event_id))

    return messages.EventProperties(
        event_id=event_id,
        calendar_id=cal_id,
        name=result["summary"],
        start_date=start_date,
        end_date=end_date,
        hidden=False,
        starred=False,
    )
