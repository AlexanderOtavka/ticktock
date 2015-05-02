'''Facilities for authenticating a user.'''


import endpoints


@wrapt.decorator
def required(func, instance, args, kwargs):
    current_user = endpoints.get_current_user()
    if current_user is None:
        raise endpoints.UnauthorizedException('Invalid token.')
    return func(*args, **kwargs)
