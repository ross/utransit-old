#
#
#

from operator import itemgetter
from xmltodict import parse
from www.info.models import Arrival, Direction, Route, Stop
from .utils import RateLimitedSession

class Ter(object):
    url = 'http://ms.api.ter-sncf.com'

    def __init__(self, agency):
        self.agency = agency
        self.session = RateLimitedSession()

    def routes(self):

        params = {'Action': 'RouteList'}
        resp = self.session.get(self.url, params=params)


        data = parse(resp.content)['ActionRouteList']['RouteList']['Route']
        routes = {}
        stops = {}
        for route in data:
            line = route['Line']
            id = Route.create_id(self.agency.id, line['@LineId'])
            if id not in routes:
                # TODO route_type from line['ModeType']['@ModeTypeIdx']
                routes[id] = (line['@SortOrder'],
                              Route(id=id, agency=self.agency,
                                    name=line['@LineName'],
                                    sign=line['@LineId']))

        return [r[1] for r in sorted(routes.values(), key=itemgetter(0))]
