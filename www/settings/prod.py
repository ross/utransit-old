#
#
#

# Django settings for www project.

from __future__ import absolute_import

from ..settings import *

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gtfs',
        'USER': 'gtfs',
        'PASSWORD': 'gtfs',
    }
}

ALLOWED_HOSTS = ['demo.xormedia.com']
SESSION_COOKIE_SECURE = False
