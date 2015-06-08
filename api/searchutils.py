'''Tools to help with searching and sorting API data.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


class NullSearchError(Exception):
    def __init__(self):
        super(NullSearchError, self).__init__('Insufficient matches found for data item.')

def _get_kw_score(event, keywords, narrow=False):
    '''Get a relevance score for an event based on keyword matches.

    Parameters:
        event (messages.Event): The event to be scored.
        keywords (string): Search terms separated by spaces.
        narrow (boolean): If true, throw NullSearchError for insufficient keyword matches.
    Throws:
        NullSearchError: If narrow=True and insufficient keyword matches are found.
    '''
    event_string_data = event.name
    search_set = set(keywords.split())
    matches = 0
    for keyword in search_set:
        if keyword in event_string_data:
            matches += 1
    if narrow and matches < len(search_set) // 2:
        raise NullSearchError()
    return matches

STARRED = lambda e: not e.starred
START_DATE = lambda e: e.start_date
KW_SCORE = lambda kw, narrow: lambda e: _get_kw_score(e, kw, narrow)

CHRONOLOGICAL_ORDER = (STARRED, START_DATE)
KW_CHRON_ORDER = lambda kw, narrow: (STARRED, KW_SCORE(kw, narrow), START_DATE)


def search(list_, order):
    sorted_list = []
    for i in list_:
        try:
            sorted_list.append(tuple(score(i) for score in order) + (i,))
        except NullSearchError:
            continue
    sorted_list = sorted(sorted_list)
    return list(zip(*sorted_list)[-1])

def keyword_chron_search(event_list, keywords):
    return search(event_list, KW_CHRON_ORDER(keywords, True))

def chron_sort(event_list):
    return search(event_list, CHRONOLOGICAL_ORDER)
