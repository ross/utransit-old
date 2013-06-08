#
#
#

from os.path import dirname, join
from ..settings import *

DEBUG = False

ROOT = dirname(dirname(dirname(__file__)))

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'www.api.authentication.TokenMiddlewareAuthentication'
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'www.api.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}

API_KEYS = {
    'BART': API_KEY_BART,
    'ONE_BUS_AWAY_SEA': API_KEY_ONE_BUS_AWAY_SEA,
    'ONE_BUS_AWAY_MTA': API_KEY_ONE_BUS_AWAY_MTA,
    'ONE_BUS_AWAY_GATECH': API_KEY_ONE_BUS_AWAY_GATECH,
    'ONE_BUS_AWAY_DDOT': API_KEY_ONE_BUS_AWAY_DDOT,
    'ONE_BUS_AWAY_USF': API_KEY_ONE_BUS_AWAY_USF
}

DATABASES = {
    'default': {
        'ENGINE': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

TIME_ZONE = 'America/Los_Angeles'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week

STATIC_ROOT = join(ROOT, 'www/static/')
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = 'wg6cuu+vzh19u!iz+d^^32xpm@5ix*l-0s42e&b2@&ubqv9dbq'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'www.api.middleware.ExceptionLoggingMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'www.api.middleware.TokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'www.urls'
WSGI_APPLICATION = 'www.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # our apps
    'www.gtfs',
    'www.info',
    'www.api',
    # third party apps
    'rest_framework',
    'rest_framework.authtoken',
)

LOGGING = {
    'version': 1,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)-5s %(name)s %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%SZ',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.WatchedFileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': 'django.log',
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ('console', 'file'),
    },
    'loggers': {
        'django.db.backends': {
            # comment out to see db queries
            'level': 'INFO',
        },
    },
}
