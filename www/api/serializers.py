#
#
#

from rest_framework import serializers
from www.info.models import Agency, Arrival, Direction, Region, Route, Stop


class HRefField(serializers.Field):

    def __init__(self, *args, **kwargs):
        super(HRefField, self).__init__(*args, **kwargs)
        kwargs['read_only'] = True

    def field_to_native(self, obj, field_name):
        if field_name == 'href':
            href = obj.get_absolute_url()
            return self.context['request'].build_absolute_uri(href)
        return super(HRefField, self).field_to_native(obj, field_name)


class IdOrBlankField(serializers.CharField):

    def to_native(self, obj):
        return obj.split(':')[-1] if obj else None


class DictFieldMixin(object):

    def field_to_native(self, obj, field_name):
        value = getattr(obj, self.source or field_name)
        if callable(value):
            value = value()
        return {v.get_id(): self.to_native(v) for v in value}


## ModelSerializer with just the direct properties, no associations, hrefs, and
## ids


class RegionSerializer(serializers.ModelSerializer):
    href = HRefField()

    class Meta:
        model = Region


class AgencySerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    href = HRefField()

    class Meta:
        exclude = {'provider', 'region'}
        model = Agency


class RouteSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    href = HRefField()

    class Meta:
        exclude = {'agency', 'order'}
        model = Route


class DirectionSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')

    class Meta:
        exclude = {'route', 'stops'}
        model = Direction


class StopSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    href = HRefField()

    class Meta:
        exclude = {'agency',}
        model = Stop


class ArrivalSerializer(serializers.ModelSerializer):
    destination = IdOrBlankField(source='destination_id')
    direction = IdOrBlankField(source='direction_id')

    class Meta:
        exclude = {'id', 'stop'}
        model = Arrival
