"""A resource file for all error or logging strings."""

from __future__ import division, print_function

__author__ = "Zander Otavka"


ERROR_CALENDAR_NOT_FOUND = \
    "No calendar with calendarId = '{calendar_id}' in user's list."


LOGGING_DELETE_UNBOUND_CALENDAR = \
    "Deleted: unbound Calendar entity with calendar_id = '{calendar_id}' " \
    "and user_id = '{user_id}'."

LOGGING_DELETE_UNBOUND_EVENT = \
    "Deleted: unbound Event entity with event_id = '{event_id}' and " \
    "calendar_id = '{calendar_id}' and user_id = '{user_id}'."

LOGGING_DELETE_OLD_EVENT = \
    "Deleted: old Event entity with event_id = '{event_id}' and " \
    "calendar_id = '{calendar_id}' and user_id = '{user_id}'."

LOGGING_GARBAGE_COLLECTION_SUMMARY = \
    "Deleted {old} old and {unbound} unbound entities ({total} total)."
