#
#
#

from collections import OrderedDict
from django.db import models


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


_provider_choices = (('NextBus', 'NextBus'), ('OneBusAway', 'OneBusAway'))


class Agency(models.Model):
    # TODO: create a task that scans proviers for new agencies and adds them
    #       that'll allow listing of unattached stuff so that we can add it to
    #       a region
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=128)
    sign = models.CharField(max_length=8)
    region = models.ForeignKey(Region, blank=True, null=True,
                               related_name='agencies')
    url = models.URLField(max_length=256)
    # TODO: choices to limit to valid timezone names
    timezone = models.CharField(max_length=32)
    # TODO: choices to limit to valid iso lang codes
    lang = models.CharField(max_length=2, blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    fare_url = models.URLField(max_length=256, blank=True, null=True)
    provider = models.CharField(max_length=16, choices=_provider_choices)

    @property
    def data(self):
        return {'id': self.id, 'name': self.name, 'sign': self.sign,
                'url': self.url, 'timezone': self.timezone,
                'region': self.region_id, 'lang': self.lang,
                'phone': self.phone, 'fare_url': self.fare_url}

    def __unicode__(self):
        return '{0} ({1})'.format(self.name, self.region_id)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'agencies'


#actransit = Agency('actransit', 'AC Transit', 'AC', 'sf', 'NextBus',
#                   'http://www.actransit.org/', 'America/Los_Angeles', 'en',
#                   '511',
#                   'http://www.actransit.org/rider-info/fares-tickets-passes/')
## bart
#emery = Agency('emery', 'Emery-Go-Round', 'EM', 'sf', 'NextBus',
#               'http://www.emerygoround.com/', 'America/Los_Angeles', 'en',
#               '510-451-3862')
#muni = Agency('sf-muni', 'San Francisco MUNI', 'MUNI', 'sf', 'NextBus',
#              'http://www.sfmta.com/', 'America/Los_Angeles', 'en',
#              '311', 'http://www.sfmta.com/cms/mfares/fareinfo.htm')
#
#city_of_seattle = Agency('23', 'City of Seattle', 'CoS', 'sea', 'OneBusAway',
#                         'http://www.seattle.gov/transportation/',
#                         'America/Los_Angeles', 'en', '206-684-7623')
#community_transit = Agency('29', 'Community Transit', 'CT', 'sea',
#                           'OneBusAway', 'http://www.communitytransit.org/',
#                           'America/Los_Angeles', 'en', '800-562-1379')
#metro = Agency('1', 'Metro Transit', 'METRO', 'sea', 'OneBusAway',
#               'http://metro.kingcounty.gov/', 'America/Los_Angeles', 'en',
#               '206-553-3000',
#               'http://metro.kingcounty.gov/tops/bus/fare/fare-info.html')
#seattle_childrens_hospital = Agency('sch', "Seattle Children's Hospital",
#                                    'SCH', 'sea', 'OneBusAway',
#                                    'http://seattlechildrens.org/',
#                                    'America/Los_Angeles', 'en')
#seattle_streetcar = Agency('seattle-sc', 'Seattle Streetcar', 'SS', 'sea',
#                           'NextBus', 'http://www.seattlestreetcar.org/',
#                           'America/Los_Angeles', 'en', '206.553.3000',
#                           'http://www.seattlestreetcar.org/faq.htm')
#sound_transit = Agency('40', 'Sound Transit', 'ST', 'sea', 'OneBusAway',
#                       'http://www.soundtransit.org/', 'America/Los_Angeles',
#                       'en', '888-889-6368',
#                       'http://www.soundtransit.org/Fares-and-Passes')
#agencies = {actransit.id: actransit, emery.id: emery, muni.id: muni,
#            city_of_seattle.id: city_of_seattle,
#            community_transit.id: community_transit,
#            seattle_childrens_hospital.id: seattle_childrens_hospital,
#            seattle_streetcar.id: seattle_streetcar,
#            sound_transit.id: sound_transit,
#            metro.id: metro}
#agency_lists = {'sf': (actransit, emery, muni),
#                'sea': (city_of_seattle, community_transit, metro,
#                        seattle_childrens_hospital, seattle_streetcar,
#                        sound_transit)}


class Route:

    # TODO: add region_id through all of these
    def __init__(self, id, agency_id, short_name, long_name, desc, typ,
                 url=None, color=None, text_color=None):
        self.id = id
        self.agency_id = agency_id
        self.short_name = short_name
        self.long_name = long_name
        self.desc = desc
        self.type = typ
        self.url = url
        self.color = color
        self.text_color = text_color
        self.stops = None
        self.directions = None

    @property
    def data(self):
        data = {'id': self.id, 'agency_id': self.agency_id,
                'short_name': self.short_name, 'long_name': self.long_name,
                'desc': self.desc, 'type': self.type, 'url': self.url,
                'color': self.color, 'text_color': self.text_color}
        if self.stops is not None:
            data['stops'] = self.stops
        if self.directions is not None:
            data['directions'] = self.directions
        return data

class Direction:

    def __init__(self, id, agency_id, route_id, short_name, stop_ids):
        self.id = id
        self.agency_id = agency_id
        self.route_id = route_id
        self.short_name = short_name
        self.stop_ids = stop_ids

    @property
    def data(self):
        return {'id': self.id, 'agency_id': self.agency_id,
                'route_id': self.route_id, 'short_name': self.short_name,
                'stop_ids': self.stop_ids}


class Stop:

    def __init__(self, id, agency_id, short_name, lat, lon, code=None,
                 desc=None, url=None, typ=None, wheelchair_boarding=None):
        self.id = id
        self.agency_id = agency_id
        self.short_name = short_name
        self.lat = lat
        self.lon = lon
        self.code = code
        self.desc = desc
        self.url = url
        self.type = typ
        self.wheelchair_boarding = wheelchair_boarding
        self.predictions = None

    @property
    def data(self):
        data = {'id': self.id, 'agency_id': self.agency_id,
                'short_name': self.short_name, 'lat': self.lat,
                'lon': self.lon, 'code': self.code, 'desc': self.desc,
                'url': self.url, 'type': self.type,
                'wheelchair_boarding': self.wheelchair_boarding}
        if self.predictions is not None:
            data['predictions'] = self.predictions
        return data


class Prediction:

    def __init__(self, agency_id, route_id, stop_id, away, departure=None):
        self.agency_id = agency_id
        self.route_id = route_id
        self.stop_id = stop_id
        self.away = away
        self.departure = departure

    @property
    def data(self):
        return {'agency_id': self.agency_id, 'route_id': self.route_id,
                'stop_id': self.stop_id, 'away': self.away,
                'departure': self.departure}
