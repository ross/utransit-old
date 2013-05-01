#
#
#

from collections import OrderedDict
from www.info.models import Direction, Prediction, Route, Stop
from xmltodict import parse
from .utils import RateLimitedSession
import requests

class NextBus(object):
    url = 'http://webservices.nextbus.com/service/publicXMLFeed'

    def __init__(self):
        self.session = RateLimitedSession()

    def routes(self, agency):
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
            id = Stop.create_id(route.agency.id, tag)
            stop = Stop(agency=route.agency, id=id,
                        name=stop['@title'], code=stop['@stopId'],
                        lat=stop['@lat'], lon=stop['@lon'])
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

    def predictions(self, route, stop):
        params = {'command': 'predictions', 'a': stop.agency.get_id(),
                  'r': route.get_id(), 's': stop.get_id()}

        resp = requests.get(self.url, params=params)

        predictions = []
        preds = parse(resp.content)['body']['predictions']
        if 'direction' in preds:
            for prediction in preds['direction']['prediction']:
                predictions.append(
                    Prediction(stop=stop, away=prediction['@seconds'],
                               departure=prediction['@isDeparture']))

        return predictions
