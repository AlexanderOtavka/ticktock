"""TickTock API definition."""

import endpoints

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


SCOPES = [
    # "https://www.googleapis.com/auth/plus.profile.emails.read",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/plus.me",
    "https://www.googleapis.com/auth/calendar.readonly"
]
WEB_CLIENT_ID = ""
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
