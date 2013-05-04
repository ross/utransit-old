#
#
#

from django.db import models
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
            if not (k == 'id' or k.startswith('_') or k.endswith('_id')) and \
                    getattr(self, k) != v :
                changed = True
                setattr(self, k, v)
        return changed


class Region(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
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


_provider_choices = (('NextBus', 'NextBus'), ('OneBusAway', 'OneBusAway'),
                     ('Bart', 'Bart'), ('GTFS', 'GTFS'))


class Agency(models.Model, IdMixin):
    region = models.ForeignKey(Region, related_name='agencies')
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=64)
    sign = models.CharField(max_length=12)
    timezone = models.CharField(max_length=32,
                                choices=[(tz, tz) for tz in all_timezones])
    lang = models.CharField(max_length=2, blank=True, null=True,
                            choices=_all_languages())
    site = models.URLField(max_length=256)
    phone = models.CharField(max_length=32, blank=True, null=True)
    fare_info = models.URLField(max_length=256, blank=True, null=True)
    provider = models.CharField(max_length=16, choices=_provider_choices)

    @classmethod
    def create_id(cls, region_id, id):
        return '{0}:{1}'.format(region_id, id)

    def get_absolute_url(self):
        return reverse('agency-detail', args=(self.region_id, self.get_id()))

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.region_id)

    class Meta:
        ordering = ('name',)


route_types = ('light-rail', 'subway', 'rail', 'bus', 'ferry', 'cable-car',
               'gondola', 'funicular')


class Route(models.Model, IdMixin, UpdateMixin):
    agency = models.ForeignKey(Agency, related_name='routes')
    id = models.CharField(max_length=32, primary_key=True)
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

    def get_absolute_url(self):
        return reverse('route-detail', args=(self.agency.region_id,
                                             self.agency.get_id(),
                                             self.get_id()))

    def get_stops(self):
        stops = []
        for direction in self.directions.all():
            stops.extend(direction.stops.all())
        return stops

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.agency_id)

    class Meta:
        ordering = ('order',)
        unique_together = (('agency', 'order'),)


class Direction(models.Model, IdMixin, UpdateMixin):
    route = models.ForeignKey(Route, related_name='directions')
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=64)

    stops = models.ManyToManyField('Stop', through='StopDirection',
                                   related_name='directions')

    @classmethod
    def create_id(cls, route_id, id):
        return '{0}:{1}'.format(route_id, id)

    def get_stop_ids(self):
        return [s.id.split(':')[-1] for s in self.stops.all()]

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.route_id)

    class Meta:
        ordering = ('name',)


stop_types= ('stop', 'station')


class Stop(models.Model, IdMixin, UpdateMixin):
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

    def get_absolute_url(self, route_slug=None):
        if route_slug:
            return reverse('stop-route-detail', args=(self.agency.region_id,
                                                      self.agency.get_id(),
                                                      route_slug,
                                                      self.get_id()))
        return reverse('stop-detail', args=(self.agency.region_id,
                                            self.agency.get_id(),
                                            self.get_id()))

    def get_predictions(self):
        return self._predictions

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.agency_id)

    class Meta:
        ordering = ('name',)


class StopDirection(models.Model, IdMixin):
    stop = models.ForeignKey(Stop, related_name='stop_direction_stop')
    direction = models.ForeignKey(Direction, related_name='stop_directions')
    order = models.IntegerField()

    def __str__(self):
        return '{0} ({1})'.format(self.stop_id, self.direction_id)

    class Meta:
        ordering = ('order',)
        unique_together = (('stop', 'direction'),)


prediction_units = ('seconds', 'meters')


class Prediction(models.Model):
    # TODO: no need to create a table for these, they won't be persisted
    stop = models.ForeignKey(Stop, related_name='predictions')
    away = models.IntegerField()
    unit = models.CharField(max_length=7,
                            choices=[(u, u) for u in prediction_units])
    departure = models.NullBooleanField(blank=True, null=True)

    class Meta:
        ordering = ('away',)


# TODO: do we want to connect stops directly to routes for performance?
