#
#
#

from django.db import models
from pycountry import languages
from pytz import all_timezones
from uuid import uuid4


# http://djangosnippets.org/snippets/1262/
# https://docs.djangoproject.com/en/dev/howto/custom-model-fields/
class _UUIDField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 32)
        kwargs['primary_key'] = True
        models.CharField.__init__(self, *args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        if add and not value:
            value = uuid4().hex
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(UUIDHexField, self).pre_save(model_instance, add)

    def db_type(self, connection):
        # this is somewhat mysql specific
        return 'char({0})'.format(self.max_length)


class Region(models.Model):
    id = _UUIDField()
    slug = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    sign = models.CharField(max_length=8)

    @property
    def data(self):
        return {'id': self.id, 'name': self.name, 'sign': self.sign,
                'agencies': self.agencies.all()}
        return data

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


def _all_languages():
    for l in languages:
        l = getattr(l, 'alpha2', None)
        if l:
            yield (l, l)


_provider_choices = (('NextBus', 'NextBus'), ('OneBusAway', 'OneBusAway'),
                     ('Bart', 'Bart'))


class Agency(models.Model):
    id = _UUIDField()
    region = models.ForeignKey(Region, related_name='agencies')
    slug = models.CharField(max_length=32)
    name = models.CharField(max_length=64)
    sign = models.CharField(max_length=8)
    url = models.URLField(max_length=256)
    timezone = models.CharField(max_length=32,
                                choices=[(tz, tz) for tz in all_timezones])
    lang = models.CharField(max_length=2, blank=True, null=True,
                            choices=_all_languages())
    phone = models.CharField(max_length=32, blank=True, null=True)
    fare_url = models.URLField(max_length=256, blank=True, null=True)
    provider = models.CharField(max_length=16, choices=_provider_choices)

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.region_id)

    class Meta:
        unique_together = (('region', 'slug'),)


route_types = ('light-rail', 'subway', 'rail', 'bus', 'ferry', 'cable-car',
               'gondola', 'funicular')


class Route(models.Model):
    id = _UUIDField()
    agency = models.ForeignKey(Agency, related_name='routes')
    slug = models.CharField(max_length=32)
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=10,
                            choices=[(t, t) for t in route_types])
    url = models.URLField(max_length=256, blank=True, null=True)
    color = models.CharField(max_length=len('#ffffff'), blank=True, null=True)

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.agency_id)

    class Meta:
        unique_together = (('agency', 'slug'),)


class Direction(models.Model):
    id = _UUIDField()
    route = models.ForeignKey(Route, related_name='directions')
    slug = models.CharField(max_length=32)
    name = models.CharField(max_length=64)

    stops = models.ManyToManyField('Stop', through='StopDirection',
                                   related_name='directions')

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.route_id)

    class Meta:
        unique_together = (('route', 'slug'),)


stop_types= ('stop', 'station')


class Stop(models.Model):
    id = _UUIDField()
    agency = models.ForeignKey(Agency, related_name='stops')
    slug = models.CharField(max_length=32)
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=16, blank=True, null=True)
    type = models.CharField(max_length=7,
                            choices=[(t, t) for t in stop_types])
    lat = models.FloatField()
    lon = models.FloatField()

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.agency_id)

    class Meta:
        unique_together = (('agency', 'slug'),)


class StopDirection(models.Model):
    stop = models.ForeignKey(Stop, related_name='stop_direction_stop')
    direction = models.ForeignKey(Direction, related_name='stop_directions')
    order = models.IntegerField()

    def __unicode__(self):
        return '{0} ({1})'.format(self.stop_id, self.direction_id)

    class Meta:
        ordering = ('order',)
        unique_together = (('stop', 'direction'),)


# TODO: do we want to connect stops directly to routes for performance?
