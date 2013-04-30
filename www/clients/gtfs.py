#
#
#

from www.info.models import Route


class _DummyFuture:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def result(self):
        # return ourself, we'll have the desired properties set up in __init__
        return self


class GTFS(object):

    def routes(self, agency):
        routes = Route.objects.filter(agency_id=agency.id).all()
        return _DummyFuture(routes=routes)

    def stops(self, agency, route):
        directions = route.directions.prefetch_related().all()
        stops = {}
        for direction in directions:
            stops.update({s.get_id(): s for s in direction.stops.all()})
        return _DummyFuture(directions=directions, stops=stops)
