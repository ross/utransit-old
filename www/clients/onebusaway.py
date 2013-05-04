#
#
#

from www.info.models import Direction, Prediction, Route, Stop, route_types, \
    stop_types
from .utils import RateLimitedSession, route_key
import requests


class OneBusAway(object):

    def __init__(self, agency):
        self.agency = agency

        self.session = RateLimitedSession()

        aid = agency.get_id()
        if aid == 'DDOT':
            self.url = 'http://ddot-beta.herokuapp.com/api/api/where'
            self.params = {'key': 'BETA'}
        elif aid in ('MTA NYCT', 'MTABC'):
            self.url = 'http://bustime.mta.info/api/where'
            self.params = {'key': 'a00d08e5-245d-4b58-8eee-e08aa7510e82'}
        else:
            self.url = 'http://api.onebusaway.org/api/where'
            self.params = {'key': 'e5ca6a2f-d074-4657-879e-6b572b3364bd'}

    def routes(self):
        agency = self.agency

        url = '{0}/routes-for-agency/{1}.json'.format(self.url,
                                                      agency.get_id())
        resp = self.session.get(url, params=self.params)

        routes = []
        for route in resp.json()['data']['list']:
            long_name = route['longName'] if route['longName'] else \
                route['shortName']
            color = route['color'] if route['color'] else None
            id = Route.create_id(agency.id, route['id'])
            routes.append(Route(id=id, agency=agency, sign=route['shortName'],
                                name=long_name,
                                type=route_types[int(route['type'])],
                                url=route['url'], color=color))

        routes.sort(key=route_key)
        for i, route in enumerate(routes):
            route.order = i

        return routes

    def stops(self, route):
        url = '{0}/stops-for-route/{1}.json'.format(self.url, route.get_id())
        params = dict(self.params)
        params['version'] = 2

        resp = self.session.get(url, params=params)

        # TODO: stops can be shared by agencies, but the first one to see it
        # will get it here :(
        data = resp.json()['data']
        stops = {}
        for stop in data['references']['stops']:
            stop = Stop(agency=route.agency,
                        id=Stop.create_id(route.agency.id, stop['id']),
                        name=stop['name'], lat=stop['lat'],
                        lon=stop['lon'], code=stop['code'],
                        type=stop_types[int(stop['locationType'])])
            stops[stop.id] = stop
        directions = []
        for stop_groupings in data['entry']['stopGroupings']:
            for stop_group in stop_groupings['stopGroups']:
                id = Direction.create_id(route.id, stop_group['id'])
                direction = Direction(route=route, id=id,
                                      name=stop_group['name']['name'])
                direction.stop_ids = [Stop.create_id(route.agency.id, sid)
                                      for sid in stop_group['stopIds']]
                directions.append(direction)

        return (directions, stops)

    def predictions(self, route, stop):
        url = '{0}/arrivals-and-departures-for-stop/{1}.json' \
            .format(self.url, stop.get_id())

        predictions = []
        if self.agency.id.startswith('nyc:MTA'):
            return predictions

        resp = requests.get(url, params=self.params)

        data = resp.json()
        current_time = data['currentTime']
        data = data['data']
        if 'entry' in data:
            data = data['entry']
        route_id = route.get_id()
        for arrival in data['arrivalsAndDepartures']:
            away = (arrival['predictedArrivalTime'] - current_time) / 1000.0
            if arrival['routeId'] == route_id and away >= 0:
                predictions.append(Prediction(stop=stop, away=int(away)))

        return predictions
