#
#
#

from collections import OrderedDict
from django.core.cache import cache
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
    if 'direction' in preds:
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


def _bart_route(pk, route):
    return Route(pk, 'bart', route['name'], None, None, 1, None,
                 route['color'], None)


def _bart_agency_cb(sess, resp, agency_id):
    # preserve BART's order
    routes = OrderedDict()
    for route in parse(resp.content)['root']['routes']['route']:
        color = route['color']
        pk = '{0}-{1}'.format(route['number'], color[1:])
        if color not in routes:
            routes[color] = _bart_route(pk, route)
        else:
            routes[color].id = '{0}-{1}'.format(routes[color].id,
                                                route['number'])
    resp.routes = list(routes.values())


def _bart_all_stops(sess, resp):
    data = parse(resp.content)
    stops = {}
    for station in data['root']['stations']['station']:
        stop = Stop(station['abbr'], 'bart', station['name'],
                    station['gtfs_latitude'], station['gtfs_longitude'],
                    None, None, None, 1, None)
        stops[stop.id] = stop
    resp.stops = stops


class BartAllStops:
    '''
    Returns the list of all bart stops, cached if possible, in background if
    not.
    '''

    def __init__(self):
        self._stops = cache.get('bart-all-stops')
        self._future = None
        if not self._stops:
            url = '{0}{1}'.format(Bart.url, 'stn.aspx')
            params = dict(Bart.params)
            params['cmd'] = 'stns'
            self._future = session.get(url, params=params,
                                       background_callback=_bart_all_stops)

    def get(self):
        if self._future:
            resp = self._future.result()
            self._stops = resp.stops
            cache.set('bart-all-stops', self._stops, 60 * 60 * 24)
        return self._stops


class BartStops:

    def __init__(self, route_id):
        self.route = None
        self.stops = {}
        self.directions = []

        self._all_stops = BartAllStops()

        def routeinfo_cb(sess, resp):
            data = parse(resp.content)['root']['routes']['route']
            if self.route is None:
                self.route = _bart_route(route_id, data)
            abbrs = data['config']['station']
            # will block if we don't already have an answer
            all_stops = self._all_stops.get()
            stops = []
            first = abbrs.pop(0)
            for abbr in abbrs:
                # copy over the relevant stations
                stop = all_stops[abbr]
                abbr = '{0}-{1}'.format(abbr, first)
                self.stops[abbr] = stop.clone(abbr)
                stops.append(abbr)
            direction = Direction(data['number'], 'bart', route_id,
                                  data['name'], stops)
            self.directions.append(direction)

        a, _, b = route_id.split('-')
        url = '{0}{1}'.format(Bart.url, 'route.aspx')
        params = dict(Bart.params)
        params['cmd'] = 'routeinfo'
        params['route'] = a
        self._future_a = session.get(url, params=params,
                                     background_callback=routeinfo_cb)
        params = dict(Bart.params)
        params['cmd'] = 'routeinfo'
        params['route'] = b
        self._future_b = session.get(url, params=params,
                                     background_callback=routeinfo_cb)

    def result(self):
        # doing these just to wait on them (work done in callbacks)
        self._future_a.result()
        self._future_b.result()

        class DummyFuture:

            def __init__(self, rt):
                self.route = rt

        route = self.route
        route.stops = self.stops
        route.directions = self.directions

        return DummyFuture(route)


def _bart_stop_cb(sess, resp, agency_id, route_id, stop_id, all_stops):
    abbr, dest = stop_id.split('-')
    resp.stop = all_stops[abbr].clone(stop_id)
    for direction in parse(resp.content)['root']['station']['etd']:
        if direction['abbreviation'] == dest:
            predictions = []
            for prediction in direction['estimate']:
                try:
                    away = int(prediction['minutes']) * 60
                except ValueError:
                    continue
                predictions.append(Prediction(agency_id, route_id, stop_id,
                                              away))
            resp.stop.predictions = predictions
            break


class Bart:
    url = 'http://api.bart.gov/api/';
    params = {'key': 'MW9S-E7SL-26DU-VV8V'};

    def routes(self, agency_id):
        url = '{0}{1}'.format(self.url, 'route.aspx')
        params = dict(self.params)
        params['cmd'] = 'routes'

        def cb_wrapper(s, r):
            _bart_agency_cb(s, r, agency_id)

        return session.get(url, params=params,
                           background_callback=cb_wrapper)

    def stops(self, agency_id, route_id):
        return BartStops(route_id)

    def stop(self, agency_id, route_id, stop_id):
        all_stops = BartAllStops().get()

        url = '{0}{1}'.format(self.url, 'etd.aspx')
        params = dict(self.params)
        params['cmd'] = 'etd'
        params['orig'] = stop_id.split('-')[0]

        def cb_wrapper(s, r):
            _bart_stop_cb(s, r, agency_id, route_id, stop_id, all_stops)

        return session.get(url, params=params,
                           background_callback=cb_wrapper)


def get_provider(id):
    if id == 'OneBusAway':
        return OneBusAway()
    elif id == 'NextBus':
        return NextBus()
    elif id == 'Bart':
        return Bart()
    raise Exception('unknown provider')
