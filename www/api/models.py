#
#
#

from collections import OrderedDict


def Region(id, name, sign):
    return {'id': id, 'name': name, 'sign': sign}


sf = Region('sf', 'San Francisco Bay Area', 'SF')
sea = Region('sea', 'Seattle Area', 'SEA')
regions = {sf['id']: sf,
           sea['id']: sea}
region_list = (sf, sea)


def Agency(id, name, sign, region, url, timezone, lang=None, phone=None,
           fare_url=None):
    return {'id': id, 'name': name, 'sign': sign, 'url': url,
            'timezone': timezone, 'region': region['id'], 'lang': lang,
            'phone': phone, 'fare_url': fare_url}


actransit = Agency('actransit', 'AC Transit', 'AC', regions['sf'],
                   'http://www.actransit.org/', 'America/Los_Angeles', 'EN',
                   '511',
                   'http://www.actransit.org/rider-info/fares-tickets-passes/')
metro = Agency('1', 'Metro Transit', 'METRO', regions['sea'],
               'http://metro.kingcounty.gov/', 'America/Los_Angeles', 'EN',
               '206-553-3000',
               'http://metro.kingcounty.gov/tops/bus/fare/fare-info.html')
agencies = {actransit['id']: actransit,
            metro['id']: metro}
agency_lists = {'sf': (actransit,),
                'sea': (metro,)}


def Route(id, agency_id, short_name, long_name, desc, type, url=None,
          color=None, text_color=None):
    return {'id': id, 'agency_id': agency_id, 'short_name': short_name,
            'long_name': long_name, 'desc': desc, 'type': type, 'url': url,
            'color': color, 'text_color': text_color}
