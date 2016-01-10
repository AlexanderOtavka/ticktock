"""TickTock API definition."""

from __future__ import division, print_function

import endpoints

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


SCOPES = [
    # "https://www.googleapis.com/auth/plus.profile.emails.read",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/plus.me",
    "https://www.googleapis.com/auth/calendar.readonly"
]
WEB_CLIENT_ID = "208366307202-00824keo9p663g1uhkd8misc52e1c5pa.apps." \
                "googleusercontent.com"
ANDROID_CLIENT_ID = ""
ANDROID_AUDIENCE = ANDROID_CLIENT_ID
IOS_CLIENT_ID = ""
ALLOWED_CLIENT_IDS = [
    endpoints.API_EXPLORER_CLIENT_ID,
]


ticktock_api = endpoints.api(
    name="ticktock", version="v1", title="TickTock API",
    scopes=SCOPES, allowed_client_ids=ALLOWED_CLIENT_IDS
)
