#
#
#

from django.db import models


class Agency(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=128)
    url = models.URLField(max_length=256)
    timezone = models.CharField(max_length=32)
    lang = models.CharField(max_length=2, blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    fare_url = models.URLField(max_length=256)


class Route(models.Model):
    agency = models.ForeignKey(Agency, related_name='routes')
    id = models.CharField(max_length=32, primary_key=True)
    short_name = models.CharField(max_length=32)
    long_name = models.CharField(max_length=128)
    desc = models.CharField(max_length=1024, null=True, blank=True)
    type = models.IntegerField()
    url = models.URLField(max_length=256, null=True, blank=True)
    color = models.CharField(max_length=8, null=True, blank=True)
    text_color = models.CharField(max_length=8, null=True, blank=True)


class Trip(models.Model):
    route = models.ForeignKey(Route, related_name='trips')
    id = models.CharField(max_length=32, primary_key=True)
    service = models.ForeignKey('Calendar', related_name='trips')
    headsign = models.CharField(max_length=32, null=True, blank=True)
    short_name = models.CharField(max_length=32)
    long_name = models.CharField(max_length=128)
    direction_id = models.IntegerField(null=True, blank=True)
    block_id = models.IntegerField(null=True, blank=True)
    shape = models.ForeignKey('Shape', null=True, blank=True)
    wheelchair_accessible = models.NullBooleanField(null=True, blank=True)


class Stop(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    code = models.CharField(max_length=32, null=True, blank=True)
    name = models.CharField(max_length=128)
    desc = models.CharField(max_length=1024, null=True, blank=True)
    lat = models.FloatField()
    lon = models.FloatField()
    zone_id = models.CharField(max_length=32, null=True, blank=True)
    url = models.URLField(max_length=256, null=True, blank=True)
    location_type = models.IntegerField(null=True, blank=True)
    parent_station = models.ForeignKey('Stop', null=True, blank=True)
    timezone = models.CharField(max_length=32, null=True, blank=True)
    wheelchair_boarding = models.NullBooleanField(null=True, blank=True)


class StopTime(models.Model):
    trip = models.ForeignKey(Trip, related_name='times')
    stop = models.ForeignKey(Stop, related_name='times')
    arrival_time = models.CharField(max_length=32)
    departure_time = models.CharField(max_length=32)
    stop_sequence = models.IntegerField()
    stop_headsign = models.CharField(max_length=32, null=True, blank=True)
    pickup_type = models.IntegerField(null=True, blank=True)
    drop_off_type = models.IntegerField(null=True, blank=True)
    shape_dist_traveled = models.FloatField(null=True, blank=True)


class Calendar(models.Model):
    service_id = models.CharField(max_length=32, primary_key=True)
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()
    saturday = models.BooleanField()
    sunday = models.BooleanField()
    start_date = models.CharField(max_length=8)
    end_date = models.CharField(max_length=8)


class CalendarDate(models.Model):
    service = models.ForeignKey(Calendar, related_name='dates')
    date = models.CharField(max_length=8)
    exception_type = models.IntegerField()


class FareAttribute(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    currency_type = models.CharField(max_length=32)
    payment_method = models.IntegerField()
    transfers = models.IntegerField(blank=True, null=True)
    transfer_duration = models.IntegerField(null=True, blank=True)


class FareRule(models.Model):
    fare = models.ForeignKey(FareAttribute, related_name='rules')
    route = models.ForeignKey(Route, related_name='fare_rules', null=True,
                              blank=True)
    origin_id = models.CharField(max_length=32, null=True, blank=True)
    destination_id = models.CharField(max_length=32, null=True, blank=True)
    contains_id = models.CharField(max_length=32, null=True, blank=True)


class Shape(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    pt_lat = models.FloatField()
    pt_lon = models.FloatField()
    pt_sequence = models.IntegerField()
    dist_traveled = models.FloatField(null=True, blank=True)


class Frequency(models.Model):
    trip = models.ForeignKey(Trip, related_name='frequencies')
    start_time = models.CharField(max_length=32)
    end_time = models.CharField(max_length=32)
    headway_secs = models.IntegerField()
    exact_times = models.NullBooleanField(null=True, blank=True)


class Transfer(models.Model):
    from_stop = models.ForeignKey(Stop, related_name='transfer_froms')
    to_stop = models.ForeignKey(Stop, related_name='transfer_tos')
    type = models.IntegerField()
    min_transfer_time = models.IntegerField(null=True, blank=True)


class FeedInfo(models.Model):
    publisher_name = models.CharField(max_length=128)
    publisher_url = models.URLField(max_length=256)
    lang = models.CharField(max_length=2, blank=True, null=True)
    start_date = models.CharField(max_length=8, null=True, blank=True)
    end_date = models.CharField(max_length=8, null=True, blank=True)
    version = models.CharField(max_length=32, blank=True, null=True)
