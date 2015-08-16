import os
import sys

LIBS = [
    os.path.join(os.path.dirname(__file__), 'libs/google-api-python-client'),
    os.path.join(os.path.dirname(__file__), 'libs/appengine-picturesque-python')
]

sys.path += LIBS
