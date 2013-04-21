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
                   'http://www.actransit.org/', 'America/Los_Angeles', 'EN',
                   '511',
                   'http://www.actransit.org/rider-info/fares-tickets-passes/')
metro = Agency('1', 'Metro Transit', 'METRO', 'sea', 'OneBusAway',
               'http://metro.kingcounty.gov/', 'America/Los_Angeles', 'EN',
               '206-553-3000',
               'http://metro.kingcounty.gov/tops/bus/fare/fare-info.html')
agencies = {actransit.id: actransit, metro.id: metro}
agency_lists = {'sf': (actransit,),
                'sea': (metro,)}


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

    @property
    def data(self):
        return {'id': self.id, 'agency_id': self.agency_id,
                'short_name': self.short_name, 'long_name': self.long_name,
                'desc': self.desc, 'type': self.type, 'url': self.url,
                'color': self.color, 'text_color': self.text_color}
