# Django settings for www project.

from __future__ import absolute_import

from django.core.exceptions import ImproperlyConfigured
from os import environ

# require ENV to be defined
if 'ENV' not in environ:
    raise ImproperlyConfigured('ENV environmental variable not specified')
env = environ['ENV']

# import our credentials, stuff that shouldn't be in scm
from creds import *

# import the based config (stuff that spans all situations)
from .base import *

# import the env specific config (stuff that's specific to what point in the
# process we're at)
# TODO: might be nice to switch this to something that dynamically loads the
# named file rather than this if/switch. downside is that you can't add other
# configs, upside is that you can't specify "bad" values
if env == 'dev':
    from .dev import *
    # import overrides, should only be used in dev, this is where you'd add
    # customizations that are just for your local box
    try:
        from .overrides import *
    except ImportError, e:
        if e.args[0] != 'No module named overrides':
            raise
elif env == 'prod':
    from .prod import *
elif env == 'integ':
    from .integ import *
elif env == 'test':
    from .test import *
else:
    raise ImproperlyConfigured('unrecognized ENV value')

lcls = locals()

if 'TEMPLATE_DEBUG' not in lcls:
    TEMPLATE_DEBUG = DEBUG

# store our configured env as a setting, though it should not be used in code
# it might be useful in logging
ENV = env
