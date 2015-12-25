"""Tools for getting data from the Google Calendar API."""

import httplib
from datetime import datetime

from endpoints import NotFoundException, ForbiddenException
from apiclient.errors import HttpError

import messages

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


CALENDAR_FIELDS = "id,summary,backgroundColor"
EVENT_FIELDS = "id,recurringEventId,summary,start,end,htmlLink"
LIST_FIELDS = "nextPageToken,items({})"


class OldEventError(Exception):
    pass


def get_calendars(service):
    """
    Return a list of the current user's calendars.

    :param service: Calendar resource object.
    :rtype: list[messages.CalendarProperties]
    :raise ForbiddenException: API request failed with status 403.
    :raise NotFoundException: API request failed with status 404.
    :raise HttpError: Other API request failure.
    """
    page_token = None
    calendars = []

    while True:
        try:
            query = service.calendarList().list(
                fields=LIST_FIELDS.format(CALENDAR_FIELDS),
                pageToken=page_token
            )
            result = query.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise NotFoundException()
            elif e.resp.status == 403:
                raise ForbiddenException()
            else:
                raise

        calendars += [
            messages.CalendarProperties(
                calendarId=item["id"],
                name=item["summary"],
                color=item["backgroundColor"],
                hidden=None
            )
            for item in result["items"]
        ]

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return calendars


def get_calendar(service, cal_id, validation_only=False):
    """
    Get a specific event by ID.

    :param service: Calendar resource object.
    :type cal_id: str
    :type validation_only: bool
    :rtype: messages.CalendarProperties
    :raise ForbiddenException: API request failed with status 403.
    :raise NotFoundException: API request failed with status 404.
    :raise HttpError: Other API request failure.
    """
    try:
        query = service.calendarList().get(
            fields="kind" if validation_only else CALENDAR_FIELDS,
            calendarId=cal_id
        )
        result = query.execute()
    except HttpError as e:
        if e.resp.status == 404:
            raise NotFoundException()
        elif e.resp.status == 403:
            raise ForbiddenException()
        else:
            raise

    if validation_only:
        return

    return messages.CalendarProperties(
        calendarId=result["id"],
        name=result["summary"],
        color=result["backgroundColor"],
        hidden=None
    )


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

    :param service: Calendar resource object.
    :type cal_id: str
    :type page_token: str
    :type time_zone: str
    :rtype: list[messages.EventProperties]
    :raise ForbiddenException: API request failed with status 403.
    :raise NotFoundException: API request failed with status 404.
    :raise HttpError: Other API request failure.
    """
    events = []
    now = datetime.utcnow().isoformat() + "Z"
    try:
        query = service.events().list(
            fields=LIST_FIELDS.format(EVENT_FIELDS),
            calendarId=cal_id,
            pageToken=page_token,
            maxResults=10,
            timeMin=now,
            timeZone=time_zone,
            singleEvents=True,
            orderBy="startTime"
        )
        result = query.execute()
    except HttpError as e:
        if e.resp.status == 404:
            raise NotFoundException()
        elif e.resp.status == 403:
            raise ForbiddenException()
        else:
            raise

    for item in result["items"]:
        if "recurringEventId" in item:
            recurrence_id = item["recurringEventId"]
        else:
            recurrence_id = None

        if "summary" in item:
            name = item["summary"]
        else:
            name = None

        assert "start" in item
        start = item["start"]
        if "dateTime" in start:
            start_date = datetime_from_string(start["dateTime"])
        else:
            start_date = datetime_from_date_string(start["date"])

        assert "end" in item
        end = item["end"]
        if "dateTime" in end:
            end_date = datetime_from_string(end["dateTime"])
        else:
            end_date = datetime_from_date_string(end["date"])

        assert "id" in item
        event = messages.EventProperties(
            eventId=item["id"],
            calendarId=cal_id,
            name=name,
            startDate=start_date,
            endDate=end_date,
            hidden=None,
            starred=None,
            link=item["htmlLink"],
            recurrenceId=recurrence_id
        )
        events.append(event)

    return events


def get_event(service, cal_id, event_id, time_zone="UTC",
              validation_only=False):
    """
    Get a specific event by ID.

    :param service: Calendar resource object.
    :type cal_id: str
    :type event_id: str
    :type time_zone: str
    :type validation_only: bool
    :rtype: messages.EventProperties
    :raise OldEventError: The requested event takes place in the past.
    :raise ForbiddenException: API request failed with status 403.
    :raise NotFoundException: API request failed with status 404.
    :raise HttpError: Other API request failure.
    """
    try:
        query = service.events().get(
            fields="end" if validation_only else EVENT_FIELDS,
            calendarId=cal_id,
            eventId=event_id,
            timeZone=time_zone
        )
        result = query.execute()
    except HttpError as e:
        if e.resp.status == httplib.NOT_FOUND:
            raise NotFoundException()
        elif e.resp.status == httplib.FORBIDDEN:
            raise ForbiddenException()
        else:
            raise

    end = result["end"]
    if "dateTime" in end:
        end_date = datetime_from_string(end["dateTime"])
    else:
        end_date = datetime_from_date_string(end["date"])

    now = datetime.utcnow()
    if end_date < now:
        raise OldEventError("Event \"{}\" ended in the past.".format(event_id))

    if validation_only:
        return

    if "recurringEventId" in result:
        recurrence_id = result["recurringEventId"]
    else:
        recurrence_id = None

    if "summary" in result:
        name = result["summary"]
    else:
        name = None

    start = result["start"]
    if "dateTime" in start:
        start_date = datetime_from_string(start["dateTime"])
    else:
        start_date = datetime_from_date_string(start["date"])

    return messages.EventProperties(
        eventId=event_id,
        calendarId=cal_id,
        name=name,
        startDate=start_date,
        endDate=end_date,
        hidden=None,
        starred=None,
        link=result["htmlLink"],
        recurrenceId=recurrence_id
    )
