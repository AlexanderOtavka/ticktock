"""The endpoints server."""
__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"

import endpoints

from calendarsapi import CalendarsAPI
from eventsapi import EventsAPI
from publicapi import PublicAPI


server = endpoints.api_server([CalendarsAPI, EventsAPI, PublicAPI])
