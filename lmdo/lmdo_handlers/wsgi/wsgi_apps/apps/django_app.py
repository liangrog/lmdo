import os
import importlib
from wsgi_apps.middleware import Middleware

def get_django():
    from django.core.wsgi import get_wsgi_application
    """Bootstrap Django app"""

    import django
    if django.VERSION[0] <= 1 and django.VERSION[1] < 7:
        # call django.setup only for django <1.7.0
        # https://github.com/django/django/commit/80d74097b4bd7186ad99b6d41d0ed90347a39b21
        django.setup()

    return Middleware(get_wsgi_application())
