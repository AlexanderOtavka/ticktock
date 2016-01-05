"""A resource file for all error or logging strings."""

from __future__ import division, print_function

__author__ = "Zander Otavka"


def error_old_event(event_id):
    return "Event with id '{}' ended in the past.".format(event_id)


def error_calendar_not_added(calendar_id):
    return "Calendar with id '{}' is not in user's list.".format(calendar_id)


def logging_delete_unbound_calendar(calendar_id, user_id):
    return ("Deleted: unbound Calendar entity with calendar_id = '{}' and "
            "user_id = '{}'.".format(calendar_id, user_id))


def logging_delete_unbound_event(event_id, calendar_id, user_id):
    return ("Deleted: unbound Event entity with event_id = '{}' and "
            "calendar_id = '{}' and user_id = '{}'."
            .format(event_id, calendar_id, user_id))


def logging_garbage_collection_summary(unbound):
    return ("Deleted {} unbound entities."
            .format(unbound))
