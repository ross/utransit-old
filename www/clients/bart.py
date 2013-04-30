#
#
#

from collections import OrderedDict
from requests_futures.sessions import FuturesSession
from www.info.models import Route, route_types
from xmltodict import parse

# TODO: share this across clients
session = FuturesSession()


def _bart_route(pk, route, agency):
    id = Route.create_id(agency.id, pk)
    return Route(id=id, agency=agency, name=route['name'], sign='XX',
                 type=1, color=route['color'])


def _bart_agency_cb(sess, resp, agency):
    # preserve BART's order
    routes = OrderedDict()
    for route in parse(resp.content)['root']['routes']['route']:
        color = route['color']
        if color not in routes:
            routes[color] = _bart_route(route['number'], route, agency)
        else:
            routes[color].id = '{0}-{1}'.format(routes[color].id,
                                                route['number'])
    resp.routes = list(routes.values())


class Bart:
    url = 'http://api.bart.gov/api/';
    params = {'key': 'MW9S-E7SL-26DU-VV8V'};

    def routes(self, agency):
        url = '{0}{1}'.format(self.url, 'route.aspx')
        params = dict(self.params)
        params['cmd'] = 'routes'

        def cb_wrapper(s, r):
            _bart_agency_cb(s, r, agency)

        return session.get(url, params=params,
                           background_callback=cb_wrapper)

