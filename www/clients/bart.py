#
#
#

from collections import OrderedDict
from django.conf import settings
from django.core.cache import cache
from www.info.models import Arrival, Direction, Route, Stop, route_types, \
    stop_types
from xmltodict import parse
from .utils import RateLimitedSession
import requests


class Bart:
    url = 'http://api.bart.gov/api/'
    params = {'key': settings.API_KEYS['BART']}

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
        dest = abbrs[-1]
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

    color_bearing_lookup = {
        '#ffff33': {'North': ('PITT', 'sf:bart:PITT-SFIA:2'),
                    'South': ('MLBR', 'sf:bart:PITT-SFIA:1')},
        '#0099cc': {'North': ('DUBL', 'sf:bart:DALY-DUBL:11'),
                    'South': ('DALY', 'sf:bart:DALY-DUBL:12')},
        '#339933': {'North': ('FRMT', 'sf:bart:DALY-FRMT:6'),
                    'South': ('DALY', 'sf:bart:DALY-FRMT:5')},
        '#ff9933': {'North': ('RICH', 'sf:bart:FRMT-RICH:3'),
                    'South': ('FRMT', 'sf:bart:FRMT-RICH:4')},
        '#ff0000': {'North': ('RICH', 'sf:bart:MLBR-RICH:8'),
                    'South': ('MLBR', 'sf:bart:MLBR-RICH:7')},
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
            # where this train is stopping
            abbr = destination['abbreviation']
            estimates = destination['estimate']
            if isinstance(estimates, OrderedDict):
                estimates = [estimates]
            for arrival in estimates:
                try:
                    away = int(arrival['minutes']) * 60
                except ValueError:
                    continue
                # the color tells us which route it is and in combination with
                # the direction tells we know the last station on the line
                color = arrival['hexcolor']
                dest, dir_id = \
                    self.color_bearing_lookup[color][arrival['direction']]
                dest_id = Stop.create_id(stop.agency_id,
                                         '{0}-{1}'.format(abbr, dest))
                arrivals.append(Arrival(stop=stop, away=away,
                                        direction_id=dir_id,
                                        destination_id=dest_id))

        return arrivals

    route_dest_to_bearing = {
        'sf:bart:PITT-SFIA': {'MLBR': ('#ffff33', 'South'),
                              'PITT': ('#ffff33', 'North')},
        'sf:bart:DALY-DUBL': {'DALY': ('#0099cc', 'South'),
                              'DUBL': ('#0099cc', 'North')},
        'sf:bart:DALY-FRMT': {'DALY': ('#339933', 'South'),
                              'FRMT': ('#339933', 'North')},
        'sf:bart:FRMT-RICH': {'FRMT': ('#ff9933', 'South'),
                              'RICH': ('#ff9933', 'North')},
        'sf:bart:MLBR-RICH': {'MLBR': ('#ff0000', 'South'),
                              'RICH': ('#ff0000', 'North')}
    }

    def _route_arrivals(self, stop, route):
        orig, dest = stop.get_id().split('-')

        url = '{0}{1}'.format(self.url, 'etd.aspx')
        params = dict(self.params)
        params['cmd'] = 'etd'
        params['orig'] = orig
        resp = requests.get(url, params=params)

        # we're looking for trains heading in which direction
        color, bearing = self.route_dest_to_bearing[route.id][dest]

        arrivals = []
        etds = parse(resp.content)['root']['station']['etd']
        if isinstance(etds, OrderedDict):
            etds = [etds]
        for direction in etds:
            dest_id = \
                Stop.create_id(stop.agency.id,
                               '{0}-{1}'.format(direction['abbreviation'],
                                                dest))
            estimates = direction['estimate']
            if isinstance(estimates, OrderedDict):
                estimates = [estimates]
            for arrival in estimates:
                # TODO: we should be looking for the right route
                if arrival['hexcolor'] == color and \
                   arrival['direction'] == bearing:
                    try:
                        away = int(arrival['minutes']) * 60
                    except ValueError:
                        continue
                    arrivals.append(Arrival(stop=stop, away=away,
                                            destination_id=dest_id))

        return arrivals

    def arrivals(self, stop, route=None):
        if route:
            return self._route_arrivals(stop, route)
        return self._stop_arrivals(stop)
