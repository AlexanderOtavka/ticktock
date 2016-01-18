"""Tools to help with searching and sorting API data."""

from __future__ import division, print_function

import locale
from functools import cmp_to_key

from messages import EventProperties, CalendarProperties

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


class NullSearchError(Exception):
    def __init__(self):
        super(NullSearchError, self).__init__(
                "Insufficient matches found for data item.")


def _get_event_kw_score(event, keywords, narrow):
    """
    Get a relevance score for an event based on keyword matches.

    :type event: EventProperties
    :type keywords: str
    :param bool narrow: If true, throw NullSearchError for insufficient keyword
                        matches.
    :rtype: float
    :raise NullSearchError: If narrow is True and insufficient keyword matches
                            are found.
    """
    # TODO: make search algorithm less bad
    event_string_data = event.name.lower()
    search_set = set(keywords.split())
    matches = 0.0
    for keyword in search_set:
        if keyword.lower() in event_string_data:
            matches += 1.0
    if narrow and (not matches or matches < len(search_set) // 2):
        raise NullSearchError()
    return matches


def _get_calendar_kw_score(calendar, keywords, narrow):
    """
    Get a relevance score for a calendar based on keyword matches.

    :param CalendarProperties calendar: Event to be scored.
    :param str keywords: Search terms separated by spaces.
    :param bool narrow:
        If true, throw NullSearchError for insufficient keyword matches.

    :rtype: int
    :raise NullSearchError:
        If narrow=True and insufficient keyword matches are found.
    """
    calendar_string_data = calendar.name
    search_set = set(keywords.split())
    matches = 0
    for keyword in search_set:
        if keyword in calendar_string_data:
            matches += 1
    if narrow and matches < len(search_set) // 2:
        raise NullSearchError()
    return matches


def event_starred(e):
    return not e.starred


def event_start_date(e):
    return e.startDate


def event_alpha_score(e):
    return cmp_to_key(locale.strcoll)(e.name.lower())


def event_id_score(e):
    # ID sorting will always return the same order, but the order is
    # meaningless so it should always be last to solve conflicts between
    # otherwise identical events.
    return e.eventId


def event_kw_score(kw, narrow):
    return lambda e: _get_event_kw_score(e, kw, narrow)


def calendar_kw_score(kw, narrow):
    return lambda c: _get_calendar_kw_score(c, kw, narrow)


def calendar_alpha_score(c):
    return cmp_to_key(locale.strcoll)(c.name.lower())


def calendar_id_score(c):
    # ID sorting will always return the same order, but the order is
    # meaningless so it should always be last to solve conflicts between
    # otherwise identical calendars.
    return c.calendarId


def search(search_list, order):
    """
    Search and sort search_list based on tuple of order functions.

    :type search_list: list[T]
    :type order: list[(T) -> object]
    :rtype: list[T]
    """
    if not search_list:
        return []
    sorted_list = []
    for i in search_list:
        try:
            # noinspection PyCallingNonCallable
            sorted_list.append(tuple(score(i) for score in order) + (i,))
        except NullSearchError:
            continue
    sorted_list = sorted(sorted_list)
    if sorted_list:
        return list(zip(*sorted_list)[-1])
    else:
        return []


def event_keyword_search(event_list, keywords):
    """
    Search exclusively by keyword order, and narrow results.

    :type event_list: list[EventProperties]
    :type keywords: str
    :rtype: list[EventProperties]
    """
    return search(event_list, [event_kw_score(keywords, True)])


def event_keyword_chron_sort(event_list, keywords):
    """
    Sort by keyword matches, then by start date, putting starred first.

    :type event_list: list[EventProperties]
    :type keywords: str
    :rtype: list[EventProperties]
    """
    return search(event_list, [event_starred, event_kw_score(keywords, False),
                               event_start_date, event_alpha_score,
                               event_id_score])


def event_chron_sort(event_list):
    """
    Sort events in chronological order, starred first.

    :type event_list: list[EventProperties]
    :rtype: list[EventProperties]
    """
    return search(event_list, [event_starred, event_start_date,
                               event_alpha_score, event_id_score])


def calendar_keyword_alpha_search(calendar_list, keywords):
    """
    Search and narrow by keyword matches, then alphabetical order.

    :type calendar_list: list[CalendarProperties]
    :type keywords: str
    :rtype: list[CalendarProperties]
    """
    return search(calendar_list, [calendar_kw_score(keywords, True),
                                  calendar_alpha_score, calendar_id_score])


def calendar_alpha_sort(calendar_list):
    """
    Sort calendars in alphabetical order.

    :type calendar_list: list[CalendarProperties]
    :rtype: list[CalendarProperties]
    """
    return search(calendar_list, [calendar_alpha_score, calendar_id_score])
