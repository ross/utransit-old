#
#
#

from collections import OrderedDict
from django.core.cache import cache
from www.info.models import Arrival, Direction, Route, Stop, route_types, \
    stop_types
from xmltodict import parse
from .utils import RateLimitedSession
import requests


class Bart:
    url = 'http://api.bart.gov/api/';
    params = {'key': 'MW9S-E7SL-26DU-VV8V'};

    def __init__(self, agency):
        self.agency = agency

        self.session = RateLimitedSession()

        self._cached_all_stops = None

    def routes(self):
        agency = self.agency

        url = '{0}{1}'.format(self.url, 'route.aspx')
        params = dict(self.params)
        params['cmd'] = 'routes'

        resp = self.session.get(url, params=params)

        # preserve BART's order
        routes = OrderedDict()
        for route in parse(resp.content)['root']['routes']['route']:
            color = route['color']
            if color not in routes:
                id = Route.create_id(agency.id, route['abbr'])
                routes[color] = Route(id=id, agency=agency, name=route['name'],
                                      sign=route['abbr'], type=route_types[1],
                                      color=route['color'],
                                      order=len(routes))

        return list(routes.values())

    def _all_stops(self):
        if self._cached_all_stops:
            return self._cached_all_stops

        url = '{0}{1}'.format(Bart.url, 'stn.aspx')
        params = dict(Bart.params)
        params['cmd'] = 'stns'

        resp = self.session.get(url, params=params)

        data = parse(resp.content)
        stops = {}
        for station in data['root']['stations']['station']:
            # don't care about having "real" ids here
            stop = Stop(agency=self.agency, id=station['abbr'],
                        name=station['name'], lat=station['gtfs_latitude'],
                        lon=station['gtfs_longitude'], type=stop_types[1])
            stops[stop.id] = stop

        self._cached_all_stops = stops

        return stops

    id_to_number = {'sf:bart:PITT-SFIA': [1, 2], 'sf:bart:DALY-DUBL': [12, 11],
                    'sf:bart:DALY-FRMT': [6, 5], 'sf:bart:FRMT-RICH': [3, 4],
                    'sf:bart:MLBR-RICH': [8, 7]}

    def _route_info(self, route, number):
        url = '{0}{1}'.format(Bart.url, 'route.aspx')
        params = dict(Bart.params)
        params['cmd'] = 'routeinfo'
        params['route'] = number

        resp = self.session.get(url, params=params)

        data = parse(resp.content)['root']['routes']['route']
        # list of stations this route passes
        abbrs = data['config']['station']
        # will block if we don't already have an answer
        all_stops = self._all_stops()
        stop_ids = []
        stops = {}
        # dest
        dest = abbrs.pop()
        for abbr in abbrs:
            # copy over the relevant stations
            stop = all_stops[abbr]
            stop = Stop(agency=route.agency,
                        id=Stop.create_id(route.agency.id,
                                          '{0}-{1}'.format(abbr, dest)),
                        name=stop.name, lat=stop.lat, lon=stop.lon,
                        type=stop.type)
            stop_ids.append(stop.id)
            stops[stop.id] = stop
        direction = Direction(route=route,
                              id=Direction.create_id(route.id, number),
                              name=data['name'].split(' - ')[1])
        direction.stop_ids = stop_ids

        return (direction, stops)

    def stops(self, route):
        a, b = self.id_to_number[route.id]
        direction_a, stops = self._route_info(route, a)
        direction_b, stps = self._route_info(route, b)
        stops.update(stps)

        return ([direction_a, direction_b], stops)

    color_dest_to_dir = {
        '#ffff33': {'MLBR': 'sf:bart:PITT-SFIA:1',
                    'PITT': 'sf:bart:PITT-SFIA:2'},
        '#0099cc': {'DUBL': 'sf:bart:DALY-DUBL:11',
                    'DALY': 'sf:bart:DALY-DUBL:12'},
        '#339933': {'DALY': 'sf:bart:DALY-FRMT:5',
                    'FRMT': 'sf:bart:DALY-FRMT:6'},
        '#ff9933': {'RICH': 'sf:bart:FRMT-RICH:3',
                    'FRMT': 'sf:bart:FRMT-RICH:4'},
        '#ff0000': {'MLBR': 'sf:bart:MLBR-RICH:7',
                    'RICH': 'sf:bart:MLBR-RICH:8'}
    }

    def _stop_arrivals(self, stop):
        abbr = stop.get_id().split('-')[0]

        url = '{0}{1}'.format(self.url, 'etd.aspx')
        params = dict(self.params)
        params['cmd'] = 'etd'
        # the station we're interested in
        params['orig'] = abbr
        resp = requests.get(url, params=params)

        arrivals = []
        etds = parse(resp.content)['root']['station']['etd']
        if isinstance(etds, OrderedDict):
            etds = [etds]
        for destination in etds:
            dest_abbr = destination['abbreviation']
            estimates = destination['estimate']
            if isinstance(estimates, OrderedDict):
                estimates = [estimates]
            for arrival in estimates:
                try:
                    away = int(arrival['minutes']) * 60
                except ValueError:
                    continue
                color = arrival['hexcolor']
                did = self.color_dest_to_dir[color][dest_abbr]
                arrivals.append(Arrival(stop=stop, away=away,
                                        direction_id=did))

        return arrivals

    def _route_abbrs(self, route, stop):
        '''finds all of the station abbrs for a given route and stop, cached
        for performance'''
        key = 'route_abbrs-{0}-{1}'.format(route.id, stop.id)
        abbrs = cache.get(key)
        if abbrs:
            return abbrs

        direction = Direction.objects.get(route=route, stops=stop)
        abbrs = [sd.stop_id.split(':')[-1].split('-')[0]
                 for sd in direction.stop_directions.all()]

        cache.set(key, abbrs)

        return abbrs

    def _route_arrivals(self, stop, route):
        orig, dest = stop.get_id().split('-')

        url = '{0}{1}'.format(self.url, 'etd.aspx')
        params = dict(self.params)
        params['cmd'] = 'etd'
        params['orig'] = orig
        resp = requests.get(url, params=params)

        # handle routes that are stopping short by finding all of the stops
        # after the current one
        laterAbbrs = set((dest,))
        later = False
        for abbr in self._route_abbrs(route, stop):
            if later:
                laterAbbrs.add(abbr)
            elif abbr == orig:
                later = True

        etds = parse(resp.content)['root']['station']['etd']
        if isinstance(etds, OrderedDict):
            etds = [etds]
        for direction in etds:
            if direction['abbreviation'] in laterAbbrs:
                arrivals = []
                estimates = direction['estimate']
                if isinstance(estimates, OrderedDict):
                    estimates = [estimates]
                for arrival in estimates:
                    try:
                        away = int(arrival['minutes']) * 60
                    except ValueError:
                        continue
                    arrivals.append(Arrival(stop=stop, away=away))
                return arrivals

        return []

    def arrivals(self, stop, route=None):
        if route:
            return self._route_arrivals(stop, route)
        return self._stop_arrivals(stop)
