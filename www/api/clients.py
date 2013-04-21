#
#
#

from requests_futures.sessions import FuturesSession
from www.api.models import Route
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
        tag = route['@tag']
        # TODO: other data, esp url, probably require pre-walk and store/cache
        routes.append(Route(tag, agency_id, route['@title'], None, None,
                            None, None, None, None))
    resp.routes = routes


class NextBus:

    def routes(self, agency_id):
        url = 'http://webservices.nextbus.com/service/publicXMLFeed';
        params = {'command': 'routeList', 'a': agency_id}

        def cb_wrapper(s, r):
            _nextbus_route_cb(s, r, agency_id)

        return session.get(url, params=params, background_callback=cb_wrapper)


def get_provider(id):
    if id == 'OneBusAway':
        return OneBusAway()
    elif id == 'NextBus':
        return NextBus()
    raise Exception('unknown provider')
