#
#

from os.path import dirname, join

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ROOT = dirname(dirname(__file__))

ADMINS = (
)
MANAGERS = ADMINS

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gtfs',
        'USER': 'gtfs',
        'PASSWORD': 'gtfs',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

ALLOWED_HOSTS = []
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
    'debug_toolbar.middleware.DebugToolbarMiddleware',
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
    'www.info',
    'www.api',
    # third party apps
    'debug_toolbar',
    'rest_framework',
    'rest_framework.authtoken',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
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

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}
