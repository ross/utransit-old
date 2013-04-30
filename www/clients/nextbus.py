#
#
#

from requests_futures.sessions import FuturesSession
from www.info.models import Route
from xmltodict import parse

# TODO: share this across clients
session = FuturesSession()


def _nextbus_agency_cb(sess, resp, agency):
    routes = []
    for route in parse(resp.content)['body']['route']:
        tag = route['@tag']
        id = Route.create_id(agency.id, tag)
        # TODO: type, url, color (may require pre-walk etc.)
        routes.append(Route(id=id, agency=agency, name=route['@title'],
                            sign=tag, type=None))
    resp.routes = routes


class NextBus(object):
    url = 'http://webservices.nextbus.com/service/publicXMLFeed'

    def routes(self, agency):
        # use external id
        params = {'command': 'routeList', 'a': agency.get_id()}

        def cb_wrapper(s, r):
            _nextbus_agency_cb(s, r, agency)

        return session.get(self.url, params=params,
                           background_callback=cb_wrapper)
