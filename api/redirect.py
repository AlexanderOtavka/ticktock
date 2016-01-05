"""The endpoints server."""

from __future__ import division, print_function

import webapp2

__author__ = "Alexander Otavka"
__copyright__ = "Copyright (C) 2015 DHS Developers Club"


class RedirectHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect("/_ah/api/explorer")


explorer_redirect = webapp2.WSGIApplication([
    ("/", RedirectHandler),
])
