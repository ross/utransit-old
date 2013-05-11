#
#
#

from collections import OrderedDict
from operator import attrgetter
from www.info.models import Arrival, Direction, Route, Stop
from xmltodict import parse
from .utils import RateLimitedSession
import requests


class NextBus(object):
    url = 'http://webservices.nextbus.com/service/publicXMLFeed'

    def __init__(self, agency):
        self.agency = agency

        self.session = RateLimitedSession()

    def routes(self):
        agency = self.agency

        # use external id
        params = {'command': 'routeList', 'a': agency.get_id()}

        resp = self.session.get(self.url, params=params)

        routes = []
        for i, route in enumerate(parse(resp.content)['body']['route']):
            tag = route['@tag']
            id = Route.create_id(agency.id, tag)
            # TODO: type, url, color (may require pre-walk etc.)
            routes.append(Route(id=id, agency=agency, name=route['@title'],
                                sign=tag, order=i))
        return routes

    def stops(self, route):
        params = {'command': 'routeConfig', 'a': route.agency.get_id(),
                  'r': route.get_id()}

        resp = self.session.get(self.url, params=params)

        data = parse(resp.content)['body']['route']
        stops = {}
        for stop in data['stop']:
            tag = stop['@tag']
            code = stop.get('@stopId', None)
            id = Stop.create_id(route.agency.id, tag)
            stop = Stop(agency=route.agency, id=id,
                        name=stop['@title'], code=code, lat=stop['@lat'],
                        lon=stop['@lon'])
            stops[stop.id] = stop
        directions = []
        ds = data['direction']
        if isinstance(ds, OrderedDict):
            # there's only one direction, xmltodict doesn't return an array
            ds = [ds]
        for direction in ds:
            if direction['@useForUI'] != 'true':
                continue
            stop_ids = [Stop.create_id(route.agency.id, stop['@tag'])
                        for stop in direction['stop']]
            id = Direction.create_id(route.id, direction['@tag'])
            direction = Direction(route=route, id=id, name=direction['@title'])
            direction.stop_ids = stop_ids
            directions.append(direction)

        return (directions, stops)

    def _stop_arrivals(self, stop):
        params = {'command': 'predictions', 'a': stop.agency.get_id(),
                  'stopId': stop.code}

        resp = requests.get(self.url, params=params)

        arrivals = []
        for predictions in parse(resp.content)['body']['predictions']:
            route_id = Route.create_id(stop.agency.id,
                                       predictions['@routeTag'])
            if 'direction' not in predictions:
                continue
            directions = predictions['direction']
            if isinstance(directions, OrderedDict):
                directions = [directions]
            for direction in directions:
                predictions = direction['prediction']
                if isinstance(predictions, OrderedDict):
                    predictions = [predictions]
                for prediction in predictions:
                    dir_id = Direction.create_id(route_id,
                                                 prediction['@dirTag'])
                    departure = prediction['@isDeparture'] == 'true'
                    arrivals.append(Arrival(stop=stop,
                                            away=int(prediction['@seconds']),
                                            direction_id=dir_id))

        arrivals.sort(key=attrgetter('away'))
        return arrivals

    def _route_arrivals(self, stop, route):
        params = {'command': 'predictions', 'a': stop.agency.get_id(),
                  's': stop.get_id(), 'r': route.get_id()}

        resp = requests.get(self.url, params=params)

        arrivals = []
        preds = parse(resp.content)['body']['predictions']
        if 'direction' in preds:
            predictions = preds['direction']['prediction']
            # TODO: come up with a helper to avoid this check everywhere
            if isinstance(predictions, OrderedDict):
                predictions = [predictions]
            for prediction in predictions:
                departure = prediction['@isDeparture'] == 'true'
                arrivals.append(Arrival(stop=stop,
                                        away=int(prediction['@seconds'])))

        return arrivals

    def arrivals(self, stop, route=None):
        if route:
            return self._route_arrivals(stop, route)
        return self._stop_arrivals(stop)
