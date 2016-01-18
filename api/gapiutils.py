"""Tools for getting data from the Google Calendar API."""

from __future__ import division, print_function

import httplib
import logging
from datetime import datetime, tzinfo

from endpoints import api_exceptions
from googleapiclient.errors import HttpError
import pytz
from oauth2client.client import AccessTokenCredentialsError

import messages
import strings

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


CALENDAR_FIELDS = "id,summary,backgroundColor"
EVENT_FIELDS = "id,recurringEventId,summary,start,end,htmlLink"
CALENDAR_LIST_FIELDS = "nextPageToken,items({})".format(CALENDAR_FIELDS)
EVENT_LIST_FIELDS = "nextPageToken,timeZone,items({})".format(EVENT_FIELDS)

HTTP_ERRORS = {
    httplib.BAD_REQUEST: api_exceptions.BadRequestException,
    httplib.UNAUTHORIZED: api_exceptions.UnauthorizedException,
    httplib.FORBIDDEN: api_exceptions.ForbiddenException,
    httplib.NOT_FOUND: api_exceptions.NotFoundException,
    httplib.CONFLICT: api_exceptions.ConflictException,
    httplib.GONE: api_exceptions.GoneException,
    httplib.PRECONDITION_FAILED: api_exceptions.PreconditionFailedException,
    httplib.REQUEST_ENTITY_TOO_LARGE:
        api_exceptions.RequestEntityTooLargeException,
    httplib.INTERNAL_SERVER_ERROR: api_exceptions.InternalServerErrorException
}


class OldEventError(api_exceptions.ForbiddenException):
    pass


def _execute_query(query):
    """
    Execute the query, and raise any errors properly.

    :param query: API query.
    """
    try:
        return query.execute()
    except HttpError as e:
        logging.error(e)
        if e.resp.status in HTTP_ERRORS:
            raise HTTP_ERRORS[e.resp.status]
        else:
            assert (e.resp.status // 100) in (4, 5)
            raise HTTP_ERRORS[e.resp.status // 100]
    except AccessTokenCredentialsError:
        # authutils.clear_stored_user_credentials()
        raise api_exceptions.UnauthorizedException("Access token expired or "
                                                   "invalid.")


def get_calendars(service):
    """
    Return a list of the current user's calendars.

    :param service: Calendar resource object.
    :rtype: list[messages.CalendarProperties]
    """
    page_token = None
    calendars = []

    while True:
        result = _execute_query(service.calendarList().list(
            fields=CALENDAR_LIST_FIELDS,
            pageToken=page_token
        ))

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
    """
    fields = "kind" if validation_only else CALENDAR_FIELDS
    result = _execute_query(service.calendarList().get(
        fields=fields,
        calendarId=cal_id
    ))

    if validation_only:
        return

    return messages.CalendarProperties(
        calendarId=result["id"],
        name=result["summary"],
        color=result["backgroundColor"],
        hidden=None
    )


def get_calendar_time_zone(service, cal_id):
    """
    Get string time zone of calendar.

    :param service: Calendar resource object.
    :type cal_id: str
    :rtype: str
    """
    return _execute_query(service.calendarList().get(
        fields="timeZone",
        calendarId=cal_id
    ))["timeZone"]


def datetime_from_string(string, time_zone):
    """
    Parse a datetime string.

    :type string: str
    :type time_zone: tzinfo
    :rtype: datetime
    """
    date_format = "%Y-%m-%dT%H:%M:%S"
    datetime_object = datetime.strptime(string[:19], date_format)
    if time_zone is not None:
        datetime_object = time_zone.localize(datetime_object)
    return datetime_object


def datetime_from_date_string(string, time_zone):
    """
    Parse a date string.

    :type string: str
    :type time_zone: tzinfo
    :rtype: datetime
    """
    date_format = "%Y-%m-%d"
    datetime_object = datetime.strptime(string[:10], date_format)
    if time_zone is not None:
        datetime_object = time_zone.localize(datetime_object)
    return datetime_object


def get_events(service, cal_id, time_zone, page_token, page_max):
    """
    Return a list of events for a given calendar.

    :param service: Calendar resource object.
    :type cal_id: str
    :type time_zone: str
    :type page_token: str
    :type page_max: int
    :rtype: (list[messages.EventProperties], str)
    """
    events = []
    result = _execute_query(service.events().list(
        fields=EVENT_LIST_FIELDS,
        calendarId=cal_id,
        pageToken=page_token,
        maxResults=page_max,
        timeMin=pytz.utc.localize(datetime.utcnow()).isoformat(),
        timeZone=time_zone,
        singleEvents=True,
        orderBy="startTime"
    ))

    tzinfo_object = pytz.timezone(time_zone or result["timeZone"])

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
            start_date = datetime_from_string(start["dateTime"], tzinfo_object)
        else:
            start_date = datetime_from_date_string(start["date"], tzinfo_object)

        assert "end" in item
        end = item["end"]
        if "dateTime" in end:
            end_date = datetime_from_string(end["dateTime"], tzinfo_object)
        else:
            end_date = datetime_from_date_string(end["date"], tzinfo_object)

        assert "id" in item
        assert "htmlLink" in item
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

    if "nextPageToken" in result:
        next_page_token = result["nextPageToken"]
    else:
        next_page_token = None

    return events, next_page_token


def get_event(service, cal_id, event_id, time_zone, validation_only=False):
    """
    Get a specific event by ID.

    :param service: Calendar resource object.
    :type cal_id: str
    :type event_id: str
    :type time_zone: str
    :type validation_only: bool
    :rtype: messages.EventProperties
    :raise OldEventError: The requested event takes place in the past.
    """
    result = _execute_query(service.events().get(
        fields=("end,recurrence" if validation_only
                else EVENT_FIELDS + ",recurrence"),
        calendarId=cal_id,
        eventId=event_id,
        timeZone=time_zone
    ))

    now = pytz.utc.localize(datetime.utcnow())

    if "recurrence" in result:
        instances = _execute_query(service.events().instances(
            fields=("timeZone,items(end)" if validation_only else
                    EVENT_LIST_FIELDS),
            calendarId=cal_id,
            eventId=event_id,
            timeZone=time_zone,
            timeMin=now.isoformat(),
            maxResults=1
        ))

        if len(instances["items"]):
            result = instances["items"][0]
        else:
            raise OldEventError(strings.error_old_event(event_id))
        tzinfo_object = pytz.timezone(time_zone or instances["timeZone"])
    else:
        tzinfo_object = pytz.timezone(time_zone or
                                      get_calendar_time_zone(service, cal_id))

    assert "end" in result
    end = result["end"]
    if "dateTime" in end:
        end_date = datetime_from_string(end["dateTime"], tzinfo_object)
    else:
        end_date = datetime_from_date_string(end["date"], tzinfo_object)

    assert end_date >= now if "instances" in locals() else True
    if end_date < now:
        raise OldEventError(strings.error_old_event(event_id))

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
        start_date = datetime_from_string(start["dateTime"], tzinfo_object)
    else:
        start_date = datetime_from_date_string(start["date"], tzinfo_object)

    return messages.EventProperties(
        eventId=result["id"],
        calendarId=cal_id,
        name=name,
        startDate=start_date,
        endDate=end_date,
        hidden=None,
        starred=None,
        link=result["htmlLink"],
        recurrenceId=recurrence_id
    )
