#
#
#

from requests import Session
from www.info.models import Direction, Route, Stop, route_types, stop_types




class OneBusAway(object):
    params = {'key': 'e5ca6a2f-d074-4657-879e-6b572b3364bd'}

    def __init__(self):
        self.session = Session()

    def routes(self, agency):
        url = 'http://api.onebusaway.org/api/where/routes-for-agency/' \
            '{0}.json'.format(agency.get_id())

        resp = self.session.get(url, params=self.params)

        routes = []
        for route in resp.json()['data']['list']:
            long_name = route['longName'] if route['longName'] else None
            color = route['color'] if route['color'] else None
            id = Route.create_id(agency.id, route['id'])
            routes.append(Route(id=id, agency=agency, sign=route['shortName'],
                                name=long_name,
                                type=route_types[int(route['type'])],
                                url=route['url'], color=color))

        return routes

    def stops(self, route):
        url = 'http://api.onebusaway.org/api/where/stops-for-route/' \
            '{0}.json'.format(route.get_id())
        params = dict(self.params)
        params['version'] = 2

        resp = self.session.get(url, params=params)

        data = resp.json()['data']
        stops = {}
        for stop in data['references']['stops']:
            stop = Stop(agency=route.agency,
                        id=Stop.create_id(route.id, stop['id']),
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
