#
#
#

from django.db import models
from pycountry import languages
from pytz import all_timezones


class Region(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
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
                     ('Bart', 'Bart'), ('GTFS', 'GTFS'))


class Agency(models.Model):
    region = models.ForeignKey(Region, related_name='agencies')
    id = models.CharField(max_length=32, primary_key=True)
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

    @classmethod
    def create_id(cls, region_id, id):
        return '{0}:{1}'.format(region_id, id)

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.region_id)

    class Meta:
        ordering = ('name',)


route_types = ('light-rail', 'subway', 'rail', 'bus', 'ferry', 'cable-car',
               'gondola', 'funicular')


class Route(models.Model):
    agency = models.ForeignKey(Agency, related_name='routes')
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=64)
    sign = models.CharField(max_length=8)
    type = models.CharField(max_length=10,
                            choices=[(t, t) for t in route_types])
    url = models.URLField(max_length=256, blank=True, null=True)
    color = models.CharField(max_length=len('#ffffff'), blank=True, null=True)
    order = models.IntegerField()

    @classmethod
    def create_id(cls, agency_id, id):
        return '{0}:{1}'.format(agency_id, id)

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.agency_id)

    class Meta:
        ordering = ('order',)
        unique_together = (('agency', 'order'),)


class Direction(models.Model):
    route = models.ForeignKey(Route, related_name='directions')
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=64)

    stops = models.ManyToManyField('Stop', through='StopDirection',
                                   related_name='directions')

    @classmethod
    def create_id(cls, route_id, id):
        return '{0}:{1}'.format(route_id, id)

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.route_id)

    class Meta:
        ordering = ('name',)


stop_types= ('stop', 'station')


class Stop(models.Model):
    agency = models.ForeignKey(Agency, related_name='stops')
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=16, blank=True, null=True)
    type = models.CharField(max_length=7, choices=[(t, t) for t in stop_types],
                            blank=True, null=True)
    lat = models.FloatField()
    lon = models.FloatField()

    @classmethod
    def create_id(cls, agency_id, id):
        return '{0}:{1}'.format(agency_id, id)

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.agency_id)

    class Meta:
        ordering = ('name',)
        unique_together = (('agency', 'code'),)


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
