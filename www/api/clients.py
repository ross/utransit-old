#
#
#

from requests_futures.sessions import FuturesSession
from www.api.models import Route


session = FuturesSession()


def _route_cb(sess, resp):
    json = resp.json()
    routes = []
    for route in json['data']['list']:
        long_name = route['longName'] if route['longName'] else None
        color = route['color'] if route['color'] else None
        text_color = route['textColor'] if route['textColor'] else None
        routes.append(Route(route['id'], route['agencyId'],
                            route['shortName'], long_name,
                            route['description'], route['type'], route['url'],
                            color, text_color))

    resp.routes = routes


class OneBusAway:

    def routes(self, agency):
        url = 'http://api.onebusaway.org/api/where/routes-for-agency/' \
            '{0}.json'.format(agency)
        params = {'key': 'e5ca6a2f-d074-4657-879e-6b572b3364bd'}
        return session.get(url, params=params, background_callback=_route_cb)



class NextBus:
    pass


def get_provider(id):
    if id == 'OneBusAway':
        return OneBusAway()
    raise Exception('unknown provider')
