#
#
#

from requests_futures.sessions import FuturesSession
from www.api.models import Direction, Route, Stop
from xmltodict import parse


session = FuturesSession()


def _onebus_route_cb(sess, resp):
    routes = []
    for route in resp.json()['data']['list']:
        long_name = route['longName'] if route['longName'] else None
        color = route['color'] if route['color'] else None
        text_color = route['textColor'] if route['textColor'] else None
        routes.append(Route(route['id'], route['agencyId'],
                            route['shortName'], long_name,
                            route['description'], route['type'], route['url'],
                            color, text_color))

    resp.routes = routes


class OneBusAway:

    def routes(self, agency_id):
        url = 'http://api.onebusaway.org/api/where/routes-for-agency/' \
            '{0}.json'.format(agency_id)
        params = {'key': 'e5ca6a2f-d074-4657-879e-6b572b3364bd'}
        return session.get(url, params=params,
                           background_callback=_onebus_route_cb)


def _nextbus_route_cb(sess, resp, agency_id):
    routes = []
    for route in parse(resp.content)['body']['route']:
        # TODO: other data, esp url, probably require pre-walk and store/cache,
        # or ingestion of GTFS data
        routes.append(Route(route['@tag'], agency_id, route['@title'], None,
                            None, None, None, None, None))
    resp.routes = routes


def _nextbus_stop_cb(sess, resp, agency_id, route_id):
    data = parse(resp.content)['body']['route']
    stops = {}
    for stop in data['stop']:
        stop = Stop(stop['@tag'], agency_id, stop['@title'], stop['@lat'],
                    stop['@lon'])
        stops[stop.id] = stop
    resp.stops = stops
    directions = []
    for direction in data['direction']:
        if direction['@useForUI'] != 'true':
            continue
        stop_ids = [stop['@tag'] for stop in direction['stop']]
        directions.append(Direction(direction['@tag'], agency_id, route_id,
                                    direction['@title'], stop_ids))
    resp.directions = directions
    route = Route(data['@tag'], agency_id, data['@tag'], data['@title'],
                      None, None, None, data['@color'], None)
    route.directions = directions
    route.stops = stops
    resp.route = route


class NextBus:
    url = 'http://webservices.nextbus.com/service/publicXMLFeed'

    def routes(self, agency_id):
        params = {'command': 'routeList', 'a': agency_id}

        def cb_wrapper(s, r):
            _nextbus_route_cb(s, r, agency_id)

        return session.get(self.url, params=params,
                           background_callback=cb_wrapper)

    def stops(self, agency_id, route_id):
        params = {'command': 'routeConfig', 'a': agency_id, 'r': route_id}

        def cb_wrapper(s, r):
            _nextbus_stop_cb(s, r, agency_id, route_id)

        return session.get(self.url, params=params,
                           background_callback=cb_wrapper)


def get_provider(id):
    if id == 'OneBusAway':
        return OneBusAway()
    elif id == 'NextBus':
        return NextBus()
    raise Exception('unknown provider')
