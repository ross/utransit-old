#
#
#

from django.db import models
from math import cos, radians
from pycountry import languages
from pytz import all_timezones
from rest_framework.reverse import reverse


class IdMixin(object):

    def get_id(self):
        return self.id.split(':')[-1]


class UpdateMixin(object):

    def update(self, other):
        changed = False
        for k, v in other.__dict__.items():
            # ignore id, hidden stuff, and foreign keys
            if k == 'id' or k.startswith('_') or k.endswith('_id'):
                continue
            if getattr(self, k) == v:
                continue
            setattr(self, k, v)
            changed = True
        return changed


class Region(models.Model, IdMixin):
    id = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=128)
    sign = models.CharField(max_length=12)

    @property
    def data(self):
        return {'id': self.id, 'name': self.name, 'sign': self.sign,
                'agencies': self.agencies.all()}
        return data

    def get_absolute_url(self):
        return reverse('region-detail', args=(self.id,))

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


def _all_languages():
    for l in languages:
        l = getattr(l, 'alpha2', None)
        if l:
            yield (l, l)


_provider_choices = (('NextBus', 'NextBus'), ('Bart', 'Bart'),
                     ('GTFS', 'GTFS'), ('OneBusAwayDdot', 'OneBusAwayDdot'),
                     ('OneBusAwayGaTech', 'OneBusAwayGaTech'),
                     ('OneBusAwayMta', 'OneBusAwayMta'),
                     ('OneBusAwaySea', 'OneBusAwaySea'),
                     ('OneBusAwayUsf', 'OneBusAwayUsf'))


class Agency(models.Model, IdMixin):
    region = models.ForeignKey(Region, related_name='agencies')
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=64)
    sign = models.CharField(max_length=12)
    timezone = models.CharField(max_length=32,
                                choices=[(tz, tz) for tz in all_timezones])
    lang = models.CharField(max_length=2, blank=True, null=True,
                            choices=_all_languages())
    url = models.URLField(max_length=256)
    phone = models.CharField(max_length=32, blank=True, null=True)
    fare_url = models.URLField(max_length=256, blank=True, null=True)
    provider = models.CharField(max_length=16, choices=_provider_choices)

    @classmethod
    def create_id(cls, region_id, id):
        return '{0}:{1}'.format(region_id, id)

    @classmethod
    def get_region_id(cls, agency_id):
        return agency_id.split(':')[0]

    def get_absolute_url(self):
        return reverse('agency-detail',
                       args=(self.get_region_id(self.id), self.get_id()))

    def __str__(self):
        return u'{0} ({1})'.format(self.name, self.region_id)

    class Meta:
        ordering = ('name',)


route_types = ('light-rail', 'subway', 'rail', 'bus', 'ferry', 'cable-car',
               'gondola', 'funicular')


class Route(models.Model, IdMixin, UpdateMixin):
    agency = models.ForeignKey(Agency, related_name='routes')
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=64)
    sign = models.CharField(max_length=12)
    type = models.CharField(max_length=10,
                            choices=[(t, t) for t in route_types],
                            blank=True, null=True)
    color = models.CharField(max_length=len('#ffffff'), blank=True, null=True)
    order = models.IntegerField()

    @classmethod
    def create_id(cls, agency_id, id):
        return '{0}:{1}'.format(agency_id, id)

    @classmethod
    def get_region_id(cls, route_id):
        return route_id.split(':')[0]

    @classmethod
    def get_agency_id(cls, route_id):
        return route_id.split(':')[1]

    def get_absolute_url(self):
        return reverse('route-detail',
                       args=(self.get_region_id(self.id),
                             self.get_agency_id(self.id),
                             self.get_id()))

    def __str__(self):
        return u'{0} ({1})'.format(self.name, self.agency_id)

    class Meta:
        ordering = ('order',)
        unique_together = (('agency', 'order'),)


class Direction(models.Model, IdMixin, UpdateMixin):
    route = models.ForeignKey(Route, related_name='directions')
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=64)

    stops = models.ManyToManyField('Stop', through='StopDirection',
                                   related_name='directions')

    @classmethod
    def create_id(cls, route_id, id):
        return '{0}:{1}'.format(route_id, id)

    # TODO: move to views.routes
    def get_stop_ids(self):
        return [s.stop_id.split(':')[-1]
                for s in self.stop_directions.all()]

    def __str__(self):
        return u'{0} ({1})'.format(self.name, self.route_id)

    class Meta:
        ordering = ('name',)


stop_types = ('stop', 'station')


class StopManager(models.Manager):

    def nearby(self, lat, lon, radius):
        # based on
        # http://www.scribd.com/doc/2569355/Geo-Distance-Search-with-MySQL
        # converted to meters

        # create a square to filter out stops we know are out of consideration
        # to avoid calculating their distances
        r = (radius / 110574.61087757687)
        lat_min = lat - r
        lat_max = lat + r
        r = (radius / abs(cos(radians(lat)) * 110574.61087757687))
        lon_min = lon - r
        lon_max = lon + r

        # TODO: lat & lon to radians in python?

        return Stop.objects.raw('''select * from (select s.*, 12756200 *
    asin(sqrt(pow(sin(radians(%s - lat) * 0.5), 2) +
              cos(radians(%s)) * cos(radians(lat)) *
              pow(sin(radians(%s - lon) * 0.5), 2)))
    as distance from info_stop s
    where lat between %s and %s and lon between %s and %s
    order by distance) i where distance < %s limit 20''',
                                [lat, lat, lon, lat_min, lat_max,
                                 lon_min, lon_max, radius])


class Stop(models.Model, IdMixin, UpdateMixin):
    agency = models.ForeignKey(Agency, related_name='stops')
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=16, blank=True, null=True)
    type = models.CharField(max_length=7, choices=[(t, t) for t in stop_types],
                            blank=True, null=True)
    lat = models.FloatField()
    lon = models.FloatField()

    objects = StopManager()

    @classmethod
    def create_id(cls, agency_id, id):
        return '{0}:{1}'.format(agency_id, id)

    @classmethod
    def get_region_id(cls, stop_id):
        return stop_id.split(':')[0]

    @classmethod
    def get_agency_id(cls, stop_id):
        return stop_id.split(':')[1]

    def get_absolute_url(self, route_slug=None):
        if route_slug:
            return reverse('stop-route-detail',
                           args=(self.get_region_id(self.id),
                                 self.get_agency_id(self.id),
                                 route_slug, self.get_id()))
        return reverse('stop-detail', args=(self.get_region_id(self.id),
                                            self.get_agency_id(self.id),
                                            self.get_id()))

    def __str__(self):
        return u'{0} ({1})'.format(self.name, self.agency_id)

    class Meta:
        index_together = (('lat', 'lon'),)
        ordering = ('name',)


class StopDirection(models.Model, IdMixin):
    stop = models.ForeignKey(Stop, related_name='stop_direction_stop')
    direction = models.ForeignKey(Direction, related_name='stop_directions')
    order = models.IntegerField()

    def __str__(self):
        return u'{0} ({1})'.format(self.stop_id, self.direction_id)

    class Meta:
        ordering = ('order',)
        unique_together = (('stop', 'direction'),)


arrival_units = ('seconds', 'meters')
arrival_types = ('realtime', 'scheduled')


class Arrival(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    stop = models.ForeignKey(Stop, related_name='arrivals')
    direction = models.ForeignKey(Direction, blank=True, null=True)
    destination = models.ForeignKey(Stop)
    away = models.IntegerField()
    unit = models.CharField(max_length=7, default=arrival_units[0],
                            choices=[(u, u) for u in arrival_units])
    type = models.CharField(max_length=9, default=arrival_types[0],
                            choices=[(t, t) for t in arrival_types])

    class Meta:
        ordering = ('away',)
