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


class NearbyStopDirectionSerializer(DirectionSerializer):
    route = serializers.Field(source='route.get_id')

    class Meta(DirectionSerializer.Meta):
        exclude = DirectionSerializer.Meta.exclude - {'route',}


class NearbyStopSerializer(StopSerializer):
    agency = serializers.Field(source='agency.get_id')
    distance = serializers.Field()
    directions = NearbyStopDirectionSerializer(many=True)

    class Meta(StopSerializer.Meta):
        exclude = StopSerializer.Meta.exclude - {'agency',}


class NearbyRouteSerializer(DictFieldMixin, RouteSerializer):
    agency = serializers.Field(source='agency.get_id')

    class Meta(RouteSerializer.Meta):
        exclude = RouteSerializer.Meta.exclude - {'agency',}


class NearbyAgencySerializer(DictFieldMixin, AgencySerializer):
    region = serializers.Field(source='region.get_id')

    class Meta(AgencySerializer.Meta):
        exclude = AgencySerializer.Meta.exclude - {'region',}


class NearbyRegionSerializer(DictFieldMixin, RegionSerializer):

    class Meta(RegionSerializer.Meta):
        pass


class NearbySerializer(serializers.Serializer):
    stops = NearbyStopSerializer(many=True)
    regions = NearbyRegionSerializer(many=True)
    agencies = NearbyAgencySerializer(many=True)
    routes = NearbyRouteSerializer(many=True)


class NearbyDetail(NoParsesMixin, generics.RetrieveAPIView):
    model = Stop
    serializer_class = NearbySerializer

    def retrieve(self, request, region=None, agency=None, *args, **kwargs):
        try:
            lat = float(request.GET['lat'])
            lon = float(request.GET['lon'])
            radius = float(request.GET.get('radius', 500.0))
            if radius < 0 or 5000 < radius:
                # TODO: bad request, invalid param
                raise Exception('invalid radius')
        except KeyError:
            # TODO: bad request, missing param
            raise
        except ValueError:
            # TODO: bad request, bad param
            raise

        # we'll at most return 30 stops
        stops = Stop.objects.nearby(lat, lon, radius)[:20]

        if region and agency:
            agency_id = Agency.create_id(region, agency)

            def desired_agency(stop):
                return stop.agency_id == agency_id

            stops = filter(desired_agency, stops)

        prefetch_related_objects(stops, ['agency', 'agency__region',
                                         'directions', 'directions__route'])

        routes = {}
        agencies = {}
        regions = {}
        for stop in stops:
            agency = stop.agency
            agencies[agency.id] = agency
            region = agency.region
            regions[region.id] = region
            for direction in stop.directions.all():
                route = direction.route
                routes[route.id] = direction.route

        self.object = Adapter(self, agencies=agencies.values(),
                              regions=regions.values(), routes=routes.values(),
                              stops=stops)

        serializer = self.get_serializer(self.object)
        return Response(serializer.data)
