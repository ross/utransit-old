#
#
#

from django.db.models.query import prefetch_related_objects
from django.http import Http404
from django.shortcuts import get_object_or_404
from operator import attrgetter
from rest_framework import generics, serializers
from rest_framework.response import Response
from www.clients import get_provider
from www.info.models import Agency, Route, Stop
from .mixins import NoParsesMixin
from .utils import Adapter
from ..serializers import AgencySerializer, ArrivalSerializer, \
    DictFieldMixin, DirectionSerializer, RegionSerializer, RouteSerializer, \
    StopSerializer


class StopAdapter(Adapter):

    def stops(self):
        stop_ids = set([a.destination_id for a in self.arrivals])
        return Stop.objects.filter(id__in=stop_ids)


## Agency Stop


class AgencyStopAgencySerializer(AgencySerializer):
    region = RegionSerializer()

    class Meta(AgencySerializer.Meta):
        exclude = AgencySerializer.Meta.exclude - {'region',}


class StopStopSerializer(DictFieldMixin, StopSerializer):

    class Meta(StopSerializer.Meta):
        pass


class AgencyStopArrivalSerializer(ArrivalSerializer):
    route = serializers.Field(source='direction.route.get_id')

    class Meta(ArrivalSerializer.Meta):
        pass


class AgencyStopDirectionSerializer(DirectionSerializer):

    class Meta(DirectionSerializer.Meta):
        exclude = DirectionSerializer.Meta.exclude


class AgencyStopRouteSerializer(DictFieldMixin, RouteSerializer):
    directions = AgencyStopDirectionSerializer(many=True)

    class Meta(RouteSerializer.Meta):
        pass


class AgencyStopSerializer(StopSerializer):
    agency = AgencyStopAgencySerializer()
    arrivals = AgencyStopArrivalSerializer(many=True)
    # set of routes that are in arrivals
    routes = AgencyStopRouteSerializer(many=True)
    # set of stops that are destinations for arrivals
    stops = StopStopSerializer(many=True)

    class Meta(StopSerializer.Meta):
        exclude = StopSerializer.Meta.exclude - {'agency',}


class AgencyStopDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A Stop's details for a specific agency
    '''
    model = Stop
    serializer_class = AgencyStopSerializer

    def retrieve(self, request, region, agency, pk):
        try:
            stop = Stop.objects.select_related('agency') \
                .get(pk=Stop.create_id(Agency.create_id(region, agency), pk))
        except Stop.DoesNotExist:
            raise Http404('No Route matches the given query.')
        agency = stop.agency
        arrivals = get_provider(stop.agency).arrivals(stop)
        # odd if we have a mixture of units, but we currently don't so...
        # sort the arrivals
        arrivals.sort(key=attrgetter('away'))
        # never return more than 15 arrivals, limit before the prefetch to
        # avoid extra work
        arrivals = arrivals[:15]
        prefetch_related_objects(arrivals, ['direction__route__directions'])

        routes = {}
        for arrival in arrivals:
            if arrival.direction:
                route = arrival.direction.route
                routes[route.id] = route

        self.object = StopAdapter(stop, arrivals=arrivals,
                                  routes=routes.values())
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)


## Route Stop


class RouteStopAgencySerializer(AgencySerializer):
    region = RegionSerializer()

    class Meta(AgencySerializer.Meta):
        exclude = AgencySerializer.Meta.exclude - {'region',}


class RouteStopRouteSerializer(RouteSerializer):
    agency = RouteStopAgencySerializer()

    class Meta(RouteSerializer.Meta):
        exclude = RouteSerializer.Meta.exclude - {'agency',}


class RouteStopArrivalSerializer(ArrivalSerializer):

    class Meta(ArrivalSerializer.Meta):
        exclude = ArrivalSerializer.Meta.exclude | {'direction',}


class RouteStopDetailSerializer(StopSerializer):
    # the list of arrivals
    arrivals = RouteStopArrivalSerializer(many=True)
    # the route we're currently looking at
    # TODO: this should be direction
    route = RouteStopRouteSerializer()
    # set of stops that are destinations for arrivals
    stops = StopStopSerializer(many=True)

    class Meta(StopSerializer.Meta):
        pass


class RouteStopDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A Stop's details for a specific Route
    '''
    model = Stop
    serializer_class = RouteStopDetailSerializer

    def retrieve(self, request, region, agency, route, pk):
        try:
            stop = Stop.objects.select_related('agency', 'agency__region') \
                .get(pk=Stop.create_id(Agency.create_id(region, agency), pk))
        except Stop.DoesNotExist:
            raise Http404('No Route matches the given query.')
        agency = stop.agency

        route = get_object_or_404(Route, pk=Route.create_id(agency.id, route))
        arrivals = get_provider(stop.agency).arrivals(stop, route)

        self.object = StopAdapter(stop, arrivals=arrivals, route=route)

        serializer = self.get_serializer(self.object)
        return Response(serializer.data)
