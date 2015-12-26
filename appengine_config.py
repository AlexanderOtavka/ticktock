import os
import sys

LIBS = [
    os.path.join(os.path.dirname(__file__), 'libs/google-api-python-client'),
    os.path.join(os.path.dirname(__file__), 'libs/picturesque'),
    os.path.join(os.path.dirname(__file__), 'libs/pytz'),
]

sys.path += LIBS
