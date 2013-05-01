#
#
#

from requests import Session
from www.info.models import Direction, Route, Stop
from xmltodict import parse


class NextBus(object):
    url = 'http://webservices.nextbus.com/service/publicXMLFeed'

    def __init__(self):
        self.session = Session()

    def routes(self, agency):
        # use external id
        params = {'command': 'routeList', 'a': agency.get_id()}

        resp = self.session.get(self.url, params=params)

        routes = []
        for route in parse(resp.content)['body']['route']:
            tag = route['@tag']
            id = Route.create_id(agency.id, tag)
            # TODO: type, url, color (may require pre-walk etc.)
            routes.append(Route(id=id, agency=agency, name=route['@title'],
                                sign=tag, type=None))
        return routes

    def stops(self, route):
        params = {'command': 'routeConfig', 'a': route.agency.get_id(),
                  'r': route.get_id()}

        resp = self.session.get(self.url, params=params)

        data = parse(resp.content)['body']['route']
        stops = {}
        for stop in data['stop']:
            tag = stop['@tag']
            stop = Stop(agency=route.agency, id=Stop.create_id(route.id, tag),
                        name=stop['@title'], code=stop['@stopId'],
                        lat=stop['@lat'], lon=stop['@lon'])
            stops[stop.id] = stop
        directions = []
        for direction in data['direction']:
            if direction['@useForUI'] != 'true':
                continue
            stop_ids = [Stop.create_id(route.agency, stop['@tag'])
                        for stop in direction['stop']]
            id = Direction.create_id(route.id, direction['@tag'])
            direction = Direction(route=route, id=id, name=direction['@title'])
            direction.stop_ids = stop_ids
            directions.append(direction)

        return (directions, stops)
