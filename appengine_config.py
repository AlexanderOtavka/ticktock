import os
import sys

LIBS = [
    # NOTE: remove endpoints-proto-datastore with 1.0 if still unused
    os.path.join(os.path.dirname(__file__), 'libs/endpoints-proto-datastore'),
    os.path.join(os.path.dirname(__file__), 'libs/google-api-python-client'),
    os.path.join(os.path.dirname(__file__), 'libs/appengine-picturesque-python'),
    os.path.join(os.path.dirname(__file__), 'libs/wrapt'),
    ]
sys.path += LIBS
