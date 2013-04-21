#
#
#

from collections import OrderedDict


class Region:

    def __init__(self, id, name, sign):
        self.id = id
        self.name = name
        self.sign = sign

    @property
    def data(self):
        return {'id': self.id, 'name': self.name, 'sign': self.sign}


sf = Region('sf', 'San Francisco Bay Area', 'SF')
sea = Region('sea', 'Seattle Area', 'SEA')
regions = {sf.id: sf, sea.id: sea}
region_list = (sf, sea)


class Agency:

    def __init__(self, id, name, sign, region_id, provider, url, timezone,
                 lang=None, phone=None, fare_url=None):
        self.id = id
        self.name = name
        self.sign = sign
        self.region_id = region_id
        self.provider = provider
        self.url = url
        self.timezone = timezone
        self.lang = lang
        self.phone = phone
        self.fare_url = fare_url

    @property
    def data(self):
        return {'id': self.id, 'name': self.name, 'sign': self.sign,
                'url': self.url, 'timezone': self.timezone,
                'region': self.region_id, 'lang': self.lang,
                'phone': self.phone, 'fare_url': self.fare_url}


actransit = Agency('actransit', 'AC Transit', 'AC', 'sf', 'NextBus',
                   'http://www.actransit.org/', 'America/Los_Angeles', 'en',
                   '511',
                   'http://www.actransit.org/rider-info/fares-tickets-passes/')
# bart
emery = Agency('emery', 'Emery-Go-Round', 'EM', 'sf', 'NextBus',
               'http://www.emerygoround.com/', 'America/Los_Angeles', 'en',
               '510-451-3862')
muni = Agency('sf-muni', 'San Francisco MUNI', 'MUNI', 'sf', 'NextBus',
              'http://www.sfmta.com/', 'America/Los_Angeles', 'en',
              '311', 'http://www.sfmta.com/cms/mfares/fareinfo.htm')

city_of_seattle = Agency('23', 'City of Seattle', 'CoS', 'sea', 'OneBusAway',
                         'http://www.seattle.gov/transportation/',
                         'America/Los_Angeles', 'en', '206-684-7623')
community_transit = Agency('29', 'Community Transit', 'CT', 'sea',
                           'OneBusAway', 'http://www.communitytransit.org/',
                           'America/Los_Angeles', 'en', '800-562-1379')
metro = Agency('1', 'Metro Transit', 'METRO', 'sea', 'OneBusAway',
               'http://metro.kingcounty.gov/', 'America/Los_Angeles', 'en',
               '206-553-3000',
               'http://metro.kingcounty.gov/tops/bus/fare/fare-info.html')
seattle_childrens_hospital = Agency('sch', "Seattle Children's Hospital",
                                    'SCH', 'sea', 'OneBusAway',
                                    'http://seattlechildrens.org/',
                                    'America/Los_Angeles', 'en')
seattle_streetcar = Agency('seattle-sc', 'Seattle Streetcar', 'SS', 'sea',
                           'NextBus', 'http://www.seattlestreetcar.org/',
                           'America/Los_Angeles', 'en', '206.553.3000',
                           'http://www.seattlestreetcar.org/faq.htm')
sound_transit = Agency('40', 'Sound Transit', 'ST', 'sea', 'OneBusAway',
                       'http://www.soundtransit.org/', 'America/Los_Angeles',
                       'en', '888-889-6368',
                       'http://www.soundtransit.org/Fares-and-Passes')
agencies = {actransit.id: actransit, emery.id: emery, muni.id: muni,
            city_of_seattle.id: city_of_seattle,
            community_transit.id: community_transit,
            seattle_childrens_hospital.id: seattle_childrens_hospital,
            seattle_streetcar.id: seattle_streetcar,
            sound_transit.id: sound_transit,
            metro.id: metro}
agency_lists = {'sf': (actransit, emery, muni),
                'sea': (city_of_seattle, community_transit, metro,
                        seattle_childrens_hospital, seattle_streetcar,
                        sound_transit)}


class Route:

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
        if self.stops:
            data['stops'] = self.stops
        if self.directions:
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

    @property
    def data(self):
        return {'id': self.id, 'agency_id': self.agency_id,
                'short_name': self.short_name, 'lat': self.lat,
                'lon': self.lon, 'code': self.code, 'desc': self.desc,
                'url': self.url, 'type': self.type,
                'wheelchair_boarding': self.wheelchair_boarding}
