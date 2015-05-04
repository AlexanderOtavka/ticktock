'''Facilities for authenticating a user.'''
__author__ = 'Alexander Otavka'
__copyright__ = 'Copyright (C) 2015 DHS Developers Club'


import endpoints
import wrapt


@wrapt.decorator
def required(func, instance, args, kwargs):
    current_user = endpoints.get_current_user()
    if current_user is None:
        raise endpoints.UnauthorizedException('Invalid token.')
    return func(*args, **kwargs)
