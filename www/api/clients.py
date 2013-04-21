#
#
#

from requests_futures.sessions import FuturesSession
from www.api.models import Direction, Prediction, Route, Stop
from xmltodict import parse


session = FuturesSession()

def _onebus_route(data):
    long_name = data['longName'] if data['longName'] else None
    color = data['color'] if data['color'] else None
    text_color = data['textColor'] if data['textColor'] else None
    return Route(data['id'], data['agencyId'], data['shortName'], long_name,
                 data['description'], data['type'], data['url'],
                 color, text_color)


def _onebus_agency_cb(sess, resp):
    routes = []
    for route in resp.json()['data']['list']:
        routes.append(_onebus_route(route))
    resp.routes = routes


def _onebus_route_cb(sess, resp, agency_id, route_id):
    data = resp.json()['data']
    stops = {}
    for stop in data['references']['stops']:
        stop = Stop(stop['id'], agency_id, stop['name'], stop['lat'],
                    stop['lon'], stop['code'], None, None,
                    stop['locationType'], stop['wheelchairBoarding'])
        stops[stop.id] = stop
    directions = []
    for stop_groupings in data['entry']['stopGroupings']:
        for stop_group in stop_groupings['stopGroups']:
            directions.append(Direction(stop_group['id'], agency_id, route_id,
                                        stop_group['name']['name'],
                                        stop_group['stopIds']))
    for route in data['references']['routes']:
        if route['id'] == route_id:
            route = _onebus_route(route)
            break
    route.directions = directions
    route.stops = stops
    resp.route = route


def _onebus_stop_cb(sess, resp, agency_id, route_id, stop_id):
    data = resp.json()
    current_time = data['currentTime']
    data = data['data']
    predictions = []
    for arrival in data['arrivalsAndDepartures']:
        away = (arrival['predictedArrivalTime'] - current_time) / 1000.0
        if arrival['routeId'] == route_id and away >= 0:
            predictions.append(Prediction(agency_id, route_id, stop_id, away))
    stop = data['stop']
    stop = Stop(stop_id, agency_id, stop['name'], stop['lat'], stop['lon'])
    stop.predictions = predictions
    resp.stop = stop


class OneBusAway:
    params = {'key': 'e5ca6a2f-d074-4657-879e-6b572b3364bd'}

    def routes(self, agency_id):
        url = 'http://api.onebusaway.org/api/where/routes-for-agency/' \
            '{0}.json'.format(agency_id)
        return session.get(url, params=self.params,
                           background_callback=_onebus_agency_cb)

    def stops(self, agency_id, route_id):
        url = 'http://api.onebusaway.org/api/where/stops-for-route/' \
            '{0}.json'.format(route_id)
        params = dict(self.params)
        params['version'] = 2

        def cb_wrapper(s, r):
            _onebus_route_cb(s, r, agency_id, route_id)

        return session.get(url, params=params,
                           background_callback=cb_wrapper)

    def stop(self, agency_id, route_id, stop_id):
        url = 'http://api.onebusaway.org/api/where/' \
            'arrivals-and-departures-for-stop/{0}.json'.format(stop_id)

        def cb_wrapper(s, r):
            _onebus_stop_cb(s, r, agency_id, route_id, stop_id)

        return session.get(url, params=self.params,
                           background_callback=cb_wrapper)


def _nextbus_agency_cb(sess, resp, agency_id):
    routes = []
    for route in parse(resp.content)['body']['route']:
        # TODO: other data, esp url, probably require pre-walk and store/cache,
        # or ingestion of GTFS data
        routes.append(Route(route['@tag'], agency_id, route['@title'], None,
                            None, None, None, None, None))
    resp.routes = routes


def _nextbus_route_cb(sess, resp, agency_id, route_id):
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


def _nextbus_stop_cb(sess, resp, agency_id, route_id, stop_id):
    predictions = []
    preds = parse(resp.content)['body']['predictions']
    for prediction in preds['direction']['prediction']:
        predictions.append(Prediction(agency_id, route_id, stop_id,
                                      prediction['@seconds'],
                                      prediction['@isDeparture']))
    # TODO: don't have lat/long here :(
    stop = Stop(stop_id, agency_id, preds['@stopTitle'], None, None)
    stop.predictions = predictions
    resp.stop = stop


class NextBus:
    url = 'http://webservices.nextbus.com/service/publicXMLFeed'

    def routes(self, agency_id):
        params = {'command': 'routeList', 'a': agency_id}

        def cb_wrapper(s, r):
            _nextbus_agency_cb(s, r, agency_id)

        return session.get(self.url, params=params,
                           background_callback=cb_wrapper)

    def stops(self, agency_id, route_id):
        params = {'command': 'routeConfig', 'a': agency_id, 'r': route_id}

        def cb_wrapper(s, r):
            _nextbus_route_cb(s, r, agency_id, route_id)

        return session.get(self.url, params=params,
                           background_callback=cb_wrapper)

    def stop(self, agency_id, route_id, stop_id):
        params = {'command': 'predictions', 'a': agency_id, 'r': route_id,
                  's': stop_id}

        def cb_wrapper(s, r):
            _nextbus_stop_cb(s, r, agency_id, route_id, stop_id)

        return session.get(self.url, params=params,
                           background_callback=cb_wrapper)


def get_provider(id):
    if id == 'OneBusAway':
        return OneBusAway()
    elif id == 'NextBus':
        return NextBus()
    raise Exception('unknown provider')
