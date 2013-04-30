#
#
#

from requests_futures.sessions import FuturesSession
from www.info.models import Route, route_types

# TODO: share this across clients
session = FuturesSession()


def _onebus_route(data, agency):
    long_name = data['longName'] if data['longName'] else None
    color = data['color'] if data['color'] else None
    id = Route.create_id(agency.id, data['id'])
    # TODO: sign, url
    return Route(id=id, agency=agency, sign=data['shortName'],
                 name=long_name, type=route_types[int(data['type'])],
                 url=data['url'], color=color)


def _onebus_agency_cb(sess, resp, agency):
    routes = []
    for route in resp.json()['data']['list']:
        routes.append(_onebus_route(route, agency))
    resp.routes = routes


class OneBusAway(object):
    params = {'key': 'e5ca6a2f-d074-4657-879e-6b572b3364bd'}

    def routes(self, agency):
        url = 'http://api.onebusaway.org/api/where/routes-for-agency/' \
            '{0}.json'.format(agency.get_id())

        def cb_wrapper(s, r):
            _onebus_agency_cb(s, r, agency)

        return session.get(url, params=self.params,
                           background_callback=cb_wrapper)
