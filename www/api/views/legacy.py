#
#
#

from django.db.models.query import prefetch_related_objects
from rest_framework import generics, serializers
from rest_framework.response import Response
from www.clients import get_provider
from www.info.models import Agency, Stop
from .mixins import NoParsesMixin
from .utils import Adapter
from ..serializers import AgencySerializer, DictFieldMixin, \
    DirectionSerializer, RegionSerializer, RouteSerializer, StopSerializer


class LegacyNearbySerializer(serializers.Serializer):
    agency_tag = serializers.Field(source='agency.get_id')
    #route_tag
    direction_tag = serializers.Field(source='direction.get_id')
    #stop_tag
    #stop_id
    #route_title
    #direction_title
    #stop_title
    #distance
    #lat
    #lon

meters_per_mile = 1609.34


class LegacyNearby(NoParsesMixin, generics.ListAPIView):
    permission_classes = tuple()
    model = Stop
    serializer_class = LegacyNearbySerializer

    def list(self, request, agency, lat, lon, *args, **kwargs):
        lat = float(lat)
        lon = float(lon)
        max = float(request.GET.get('max', 0.25))
        if max < 0:
            max = 0.25
        elif 1 < max:
            max = 1

        radius = max * meters_per_mile

        # we'll at most return n stops
        # TODO: limiting before filtering is bad
        stops = Stop.objects.nearby(lat, lon, radius)[:25]

        prefetch_related_objects(stops, ['agency', 'directions',
                                         'directions__route'])

        results = []
        for stop in stops:
            # this is kind of ugly, but should do the trick since we don't know
            # the region
            if not stop.agency_id.endswith(agency):
                continue
            for direction in stop.directions.all():
                results.append({
                    'agency_tag': stop.agency.get_id(),
                    'direction_tag': direction.get_id(),
                    'route_tag': direction.route.get_id(),
                    'stop_tag': stop.get_id(),
                    'stop_id': stop.code,
                    'route_title': direction.route.name,
                    'direction_title': direction.name,
                    'stop_title': stop.name,
                    'distance': stop.distance / meters_per_mile,
                    'lat': stop.lat,
                    'lon': stop.lon
                })

                if len(results) > 25:
                    return Response(results)

        return Response(results)
