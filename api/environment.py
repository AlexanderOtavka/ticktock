"""Environment constants."""

from __future__ import division, print_function

import os
import logging

__author__ = "Zander Otavka"


if os.environ.get("SERVER_SOFTWARE", "").startswith("Development"):
    IS_DEV = True
    logging.info("-- ON DEV SERVER --")
else:
    IS_DEV = False
