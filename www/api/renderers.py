#
#
#

from django.db.models.query import QuerySet
from rest_framework import renderers
import re


re_under_to_camel = re.compile(r'[a-z]_[a-z]')


def _underscore_to_camel(match):
    return match.group()[0] + match.group()[2].upper()


def _camelize(data):
    if hasattr(data, 'data'):
        return _camelize(data.data)
    elif isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = re_under_to_camel.sub(_underscore_to_camel, key)
            new_dict[new_key] = _camelize(value)
        return new_dict
    elif isinstance(data, (tuple, QuerySet)):
        data = list(data)
        for i in range(len(data)):
            data[i] = _camelize(data[i])
        return data
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = _camelize(data[i])
        return data
    return data


class JSONRenderer(renderers.JSONRenderer):

    def render(self, data, *args, **kwargs):
        return super(JSONRenderer, self).render(_camelize(data), *args,
                                                **kwargs)
