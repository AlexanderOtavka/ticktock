'''Get data from the Google Calendar API, once a service has been generated.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


import messages


def get_personal_calendars(service):
    page_token = None
    calendars = []
    while True:
        api_query_result = service.calendarList().list(pageToken=page_token).execute()
        calendars += [
            messages.Calendar(
                calendar_id=item['id'],
                name=item['summary'],
                color=item['backgroundColor'],
                hidden=False)
            for item in api_query_result['items']]
        page_token = api_query_result.get('nextPageToken')
        if not page_token:
            break
    return calendars

def get_public_calendars():
    return []
