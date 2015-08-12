"""Tools to help with searching and sorting API data."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

from messages import Event


class NullSearchError(Exception):
    def __init__(self):
        super(NullSearchError, self).__init__("Insufficient matches found for data item.")


def _get_kw_score(event, keywords, narrow=False):
    """Get a relevance score for an event based on keyword matches.

    :param Event event: Event to be scored.
    :param str keywords: Search terms separated by spaces.
    :param bool narrow: If true, throw NullSearchError for insufficient keyword matches.

    :rtype: int
    :raise NullSearchError: If narrow=True and insufficient keyword matches are found.
    """
    event_string_data = event.name
    search_set = set(keywords.split())
    matches = 0
    for keyword in search_set:
        if keyword in event_string_data:
            matches += 1
    if narrow and matches < len(search_set) // 2:
        raise NullSearchError()
    return matches


STARRED = lambda e: float(not e.starred)
START_DATE = lambda e: float(e.start_date)
KW_SCORE = lambda kw, narrow: lambda e: float(_get_kw_score(e, kw, narrow))

CHRONOLOGICAL_ORDER = [STARRED, START_DATE]
KW_CHRON_ORDER = lambda kw, narrow: [STARRED, KW_SCORE(kw, narrow), START_DATE]


def search(list_, order):
    """Search and sort list_ based on tuple of order functions.

    :type list_: list[T]
    :type order: list[(Event) -> float]
    :rtype: list[T]
    """
    sorted_list = []
    for i in list_:
        try:
            sorted_list.append(tuple(score(i) for score in order) + (i,))
        except NullSearchError:
            continue
    sorted_list = sorted(sorted_list)
    return list(zip(*sorted_list)[-1])


def keyword_chron_search(event_list, keywords):
    """Convenience function, search with KW_CHRON_ORDER.

    :type event_list: list[Event]
    :type keywords: str
    :rtype: list[Event]
    """
    return search(event_list, KW_CHRON_ORDER(keywords, True))


def chron_sort(event_list):
    """Convenience function, search with CHRONOLOGICAL_ORDER.

    :type event_list: list[Event]
    :rtype: list[Event]
    """
    return search(event_list, CHRONOLOGICAL_ORDER)
