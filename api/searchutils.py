"""Tools to help with searching and sorting API data."""

from messages import EventProperties, CalendarProperties

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


class NullSearchError(Exception):
    def __init__(self):
        super(NullSearchError, self).__init__(
                "Insufficient matches found for data item.")


def _get_event_kw_score(event, keywords, narrow=False):
    """
    Get a relevance score for an event based on keyword matches.

    :param EventProperties event: Event to be scored.
    :param str keywords: Search terms separated by spaces.
    :param bool narrow:
        If true, throw NullSearchError for insufficient keyword matches.

    :rtype: float
    :raise NullSearchError:
        If narrow=True and insufficient keyword matches are found.
    """
    event_string_data = event.name
    search_set = set(keywords.split())
    matches = 0.0
    for keyword in search_set:
        if keyword in event_string_data:
            matches += 1.0
    if narrow and matches < len(search_set) // 2:
        raise NullSearchError()
    return matches


def _get_calendar_kw_score(calendar, keywords, narrow=False):
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


def event_name(e):
    return e.name


def event_kw_score(kw, narrow):
    return lambda e: _get_event_kw_score(e, kw, narrow)


def calendar_kw_score(kw, narrow):
    return lambda c: _get_calendar_kw_score(c, kw, narrow)


def calendar_alpha_score(c):
    return c.name


def event_chronological_order():
    return [event_starred, event_start_date, event_name]


def event_kw_chron_order(kw, narrow):
    return [event_starred, event_kw_score(kw, narrow), event_start_date,
            event_name]


def calendar_kw_alpha_order(kw, narrow):
    return [calendar_kw_score(kw, narrow), calendar_alpha_score]


def calendar_alpha_order():
    return [calendar_alpha_score]


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
    return list(zip(*sorted_list)[-1])


def event_keyword_chron_search(event_list, keywords):
    """
    Convenience function, search with event_kw_chron_order.

    :type event_list: list[EventProperties]
    :type keywords: str
    :rtype: list[EventProperties]
    """
    return search(event_list, event_kw_chron_order(keywords, True))


def event_chron_sort(event_list):
    """
    Convenience function, search with event_chronological_order.

    :type event_list: list[EventProperties]
    :rtype: list[EventProperties]
    """
    return search(event_list, event_chronological_order())


def calendar_keyword_alpha_search(calendar_list, keywords):
    """
    Convenience function, search with calendar_kw_alpha_order.

    :type calendar_list: list[CalendarProperties]
    :type keywords: str
    :rtype: list[CalendarProperties]
    """
    return search(calendar_list, calendar_kw_alpha_order(keywords, True))


def calendar_alpha_sort(calendar_list):
    """
    Convenience function, search with calendar_alpha_order.

    :type calendar_list: list[CalendarProperties]
    :rtype: list[CalendarProperties]
    """
    return search(calendar_list, calendar_alpha_order())
