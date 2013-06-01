#
#
#

from django.conf import settings
from www.info.models import Arrival, Direction, Route, Stop, arrival_types, \
    route_types, stop_types, arrival_units
from .utils import RateLimitedSession, route_key
import requests
import logging

logger = logging.getLogger(__name__)


class _OneBusAway(object):

    def __init__(self, agency):
        self.agency = agency
        self.session = RateLimitedSession()

    def _encode_id(self, id):
        return id

    def _decode_id(self, id):
        return id

    def routes(self):
        'returns a list of routes'
        agency = self.agency

        url = '{0}/routes-for-agency/{1}.json' \
            .format(self.url, self._decode_id(agency.get_id()))
        resp = self.session.get(url, params=self.params)

        routes = []
        for route in resp.json()['data']['list']:
            short_name = route['shortName']
            long_name = route['longName']

            name = ''
            if short_name and long_name.find(short_name) == -1:
                name = short_name + " - "
            name += long_name if long_name else route['description']

            color = route['color'] if route['color'] else None
            id = self._encode_id(Route.create_id(agency.id, route['id']))
            routes.append(Route(id=id, agency=agency, sign=short_name,
                                name=name,
                                type=route_types[int(route['type'])],
                                color=color))

        routes.sort(key=route_key)
        for i, route in enumerate(routes):
            route.order = i

        return routes

    def stops(self, route):
        'returns a tuple, with a list of directions, and a map of stops'
        url = '{0}/stops-for-route/{1}.json' \
            .format(self.url, self._decode_id(route.get_id()))
        params = dict(self.params)
        params['version'] = 2

        resp = self.session.get(url, params=params)

        # TODO: stops can be shared by agencies, but the first one to see it
        # will get it here :(
        data = resp.json()['data']
        stops = {}
        for stop in data['references']['stops']:
            id = self._encode_id(Stop.create_id(route.agency.id, stop['id']))
            stop = Stop(agency=route.agency,
                        id=id,
                        name=stop['name'], lat=stop['lat'],
                        lon=stop['lon'], code=stop['code'],
                        type=stop_types[int(stop['locationType'])])
            stops[stop.id] = stop
        directions = []
        for stop_groupings in data['entry']['stopGroupings']:
            for stop_group in stop_groupings['stopGroups']:
                id = self._encode_id(Direction.create_id(route.id,
                                                         stop_group['id']))
                direction = Direction(route=route, id=id,
                                      name=stop_group['name']['name'])
                direction.stop_ids = \
                    [self._encode_id(Stop.create_id(route.agency.id, sid))
                     for sid in stop_group['stopIds']]
                directions.append(direction)

        return (directions, stops)

    def _stop_arrivals(self, stop):
        'arrivals for all routes at a particular stop'
        url = '{0}/arrivals-and-departures-for-stop/{1}.json' \
            .format(self.url, self._decode_id(stop.get_id()))

        resp = requests.get(url, params=self.params)

        dirs = {}

        data = resp.json()
        current_time = data['currentTime']
        data = data['data']
        if 'entry' in data:
            data = data['entry']
        arrivals = []
        for arrival in data['arrivalsAndDepartures']:
            away = (arrival['predictedArrivalTime'] - current_time) / 1000.0
            typ = arrival_types[0]
            if away == 0:
                away = (arrival['scheduledArrivalTime'] -
                        current_time) / 1000.0
                typ = arrival_types[1]
            if away >= 0:
                dir_name = arrival['tripHeadsign']
                if dir_name not in dirs:
                    try:
                        # TODO: handle routes that are stopping short/are
                        # alternates
                        dirs[dir_name] = \
                            Direction.objects.get(name=dir_name).id
                    except Direction.DoesNotExist:
                        logger.warn('unknown direction (%s)', dir_name)
                        continue
                did = dirs[dir_name]
                arrivals.append(Arrival(stop=stop, away=int(away), type=typ,
                                        direction_id=did))

        return arrivals

    def _route_arrivals(self, stop, route):
        'arrivals for a route at a particular stop'
        url = '{0}/arrivals-and-departures-for-stop/{1}.json' \
            .format(self.url, self._decode_id(stop.get_id()))

        arrivals = []

        resp = requests.get(url, params=self.params)

        data = resp.json()
        current_time = data['currentTime']
        data = data['data']
        if 'entry' in data:
            data = data['entry']
        route_id = self._decode_id(route.get_id())
        for arrival in data['arrivalsAndDepartures']:
            away = (arrival['predictedArrivalTime'] - current_time) / 1000.0
            typ = arrival_types[0]
            if away == 0:
                away = (arrival['scheduledArrivalTime'] -
                        current_time) / 1000.0
                typ = arrival_types[1]
            if arrival['routeId'] == route_id and away >= 0:
                arrivals.append(Arrival(stop=stop, away=int(away), type=typ))

        return arrivals

    def arrivals(self, stop, route=None):
        'returns a list of arrivals'
        if route:
            return self._route_arrivals(stop, route)
        return self._stop_arrivals(stop)


class OneBusAwayDdot(_OneBusAway):
    url = 'http://ddot-beta.herokuapp.com/api/api/where'
    params = {'key': settings.API_KEYS['ONE_BUS_AWAY_DDOT']}


class OneBusAwayGaTech(_OneBusAway):
    url = 'http://onebusaway.gatech.edu/api/api/where'
    params = {'key': settings.API_KEYS['ONE_BUS_AWAY_GATECH']}


class OneBusAwayMta(_OneBusAway):
    url = 'http://bustime.mta.info/api/where'
    params = {'key': settings.API_KEYS['ONE_BUS_AWAY_MTA']}

    def _stop_arrivals(self, stop):
        url = 'http://bustime.mta.info/api/siri/stop-monitoring.json'

        # shares api keys with onebus
        params = dict(self.params)
        params['MonitoringRef'] = stop.get_id().split('_')[1]

        arrivals = []

        resp = requests.get(url, params=params)

        data = resp.json()['Siri']['ServiceDelivery']
        data = data['StopMonitoringDelivery'][0]

        for visit in data['MonitoredStopVisit']:
            visit = visit['MonitoredVehicleJourney']
            did = Direction.create_id(Route.create_id(stop.agency.id,
                                                      visit['LineRef']),
                                      visit['DirectionRef'])
            visit = visit['MonitoredCall']
            away = visit['Extensions']['Distances']['DistanceFromCall']
            arrivals.append(Arrival(stop=stop, away=int(away),
                                    unit=arrival_units[1], direction_id=did))

        return arrivals

    def _route_arrivals(self, stop, route):
        url = 'http://bustime.mta.info/api/siri/stop-monitoring.json'

        # shares api keys with onebus
        params = dict(self.params)
        params['MonitoringRef'] = stop.get_id().split('_')[1]
        params['LineRef'] = route.get_id().split('_')[1]

        arrivals = []

        resp = requests.get(url, params=params)

        data = resp.json()['Siri']['ServiceDelivery']
        data = data['StopMonitoringDelivery'][0]

        for visit in data['MonitoredStopVisit']:
            visit = visit['MonitoredVehicleJourney']['MonitoredCall']
            away = visit['Extensions']['Distances']['DistanceFromCall']
            arrivals.append(Arrival(stop=stop, away=int(away),
                                    unit=arrival_units[1]))

        return arrivals


class OneBusAwaySea(_OneBusAway):
    url = 'http://api.onebusaway.org/api/where'
    params = {'key': settings.API_KEYS['ONE_BUS_AWAY_SEA']}


class OneBusAwayUsf(_OneBusAway):
    url = 'http://onebusaway.forest.usf.edu/api/api/where'
    params = {'key': settings.API_KEYS['ONE_BUS_AWAY_USF']}

    def _encode_id(self, id):
        return id.replace('Hillsborough Area Regional Transit', 'HART')

    def _decode_id(self, id):
        return id.replace('HART', 'Hillsborough Area Regional Transit')
