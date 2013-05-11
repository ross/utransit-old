#
#
#

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.response import Response
from www.info.models import Agency, Direction, Route
from .mixins import NoParsesMixin
from .utils import Adapter
from ..serializers import AgencySerializer, DictFieldMixin, \
    DirectionSerializer, RegionSerializer, RouteSerializer, StopSerializer


class RouteDetailAgencySerializer(AgencySerializer):
    region = RegionSerializer()

    class Meta(AgencySerializer.Meta):
        exclude = AgencySerializer.Meta.exclude - {'region',}


class RouteDetailDirectionSerializer(DirectionSerializer):
    stops = serializers.Field(source='get_stop_ids')

    class Meta(DirectionSerializer.Meta):
        exclude = DirectionSerializer.Meta.exclude - {'stops',}


class RouteDetailStopSerializer(DictFieldMixin, StopSerializer):

    def to_native(self, obj):
        # since we have to add a route in to get a route specific stop
        # we need to manually compute and add the href
        ret = super(RouteDetailStopSerializer, self).to_native(obj)
        href = obj.get_absolute_url(self.context['route_slug'])
        ret['href'] = self.context['request'].build_absolute_uri(href)
        return ret

    class Meta(StopSerializer.Meta):
        pass


class RouteDetailSerializer(RouteSerializer):
    agency = RouteDetailAgencySerializer()
    directions = RouteDetailDirectionSerializer(many=True)
    stops = RouteDetailStopSerializer(many=True)

    class Meta(RouteSerializer.Meta):
        exclude = RouteSerializer.Meta.exclude - {'agency',}


class RouteDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A Route's details
    '''
    model = Route
    serializer_class = RouteDetailSerializer

    def get_serializer_context(self):
        ret = super(RouteDetail, self).get_serializer_context()
        # we need to pass our route id along to the stop serializers
        ret['route_slug'] = self.object.get_id()
        return ret

    def retrieve(self, request, region, agency, pk):
        try:
            route = Route.objects.select_related('agency', 'agency__region') \
                .prefetch_related('directions', 'directions__stops') \
                .get(pk=Route.create_id(Agency.create_id(region, agency), pk))
        except Route.DoesNotExist:
            raise Http404('No Route matches the given query.')

        stops = []
        for direction in route.directions.all():
            stops.extend(direction.stops.all())

        self.object = Adapter(route, stops=stops)
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)
