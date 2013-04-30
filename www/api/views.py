#
#
#

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from www.clients import get_provider
from www.info.models import Agency, Direction, Region, Route, Stop


class NoParsesMixin(object):

    def metadata(self, request):
        data = super(NoParsesMixin, self).metadata(request)
        # remove parses since we're read-only
        del data['parses']
        return data


class BaseView(NoParsesMixin, APIView):

    def get(self, request, *args, **kwargs):
        return Response(self.get_data(request, *args, **kwargs))


def api_root(request):
    return HttpResponseRedirect(reverse('regions-list', request=request))




class RegionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Region


class RegionList(NoParsesMixin, generics.ListAPIView):
    '''
    A list of Regions
    '''
    model = Region
    serializer_class = RegionSerializer


class AgencySerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')

    class Meta:
        exclude = ('provider',)
        model = Agency


class RegionDetailSerializer(serializers.ModelSerializer):
    agencies = AgencySerializer(many=True)

    class Meta:
        model = Region


class RegionDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A Region's details
    '''
    model = Region
    serializer_class = RegionDetailSerializer


class RouteSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')

    class Meta:
        exclude = ('agency', 'order')
        model = Route


class AgencyDetailSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    routes = RouteSerializer(many=True, source='get_routes')

    class Meta:
        exclude = ('provider',)
        model = Agency


class AgencyDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    An Agency's details
    '''
    model = Agency
    serializer_class = AgencyDetailSerializer

    def get(self, request, region, pk):
        agency = get_object_or_404(Agency, pk=Agency.create_id(region, pk))
        agency._future = get_provider(agency.provider).routes(agency)
        serializer = self.get_serializer(agency)
        return Response(serializer.data)


class DirectionSerializer(serializers.ModelSerializer):
    stops = serializers.Field(source='get_stop_ids')

    class Meta:
        exclude = ('id', 'route')
        model = Direction


class StopSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')

    def field_to_native(self, obj, field_name):
        if field_name == 'stops':
            value = getattr(obj, self.source)
            return {v.get_id(): self.to_native(v) for v in value()}
        return super(StopSerializer, self).field_to_native(obj, field_name)

    class Meta:
        exclude = ('agency',)
        model = Stop


class RouteDetailSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    directions = DirectionSerializer(many=True, source='get_directions')
    # TODO: suggest dictionary=True
    stops = StopSerializer(many=True, source='get_stops')

    class Meta:
        exclude = ('agency', 'order')
        model = Route


class RouteDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A Route's details
    '''
    model = Route
    serializer_class = RouteDetailSerializer

    def get(self, request, region, agency, pk):
        agency = get_object_or_404(Agency, pk=Agency.create_id(region, agency))
        route = get_object_or_404(Route, pk=Route.create_id(agency.id, pk))
        route._future = get_provider(agency.provider).stops(agency, route)
        serializer = self.get_serializer(route)
        return Response(serializer.data)

    def get_data(self, request, region, agency, pk):
        agency = get_object_or_404(Agency, pk=agency)
        future = get_provider(agency.provider).stops(agency.id, pk)
        return future.result().route


class RouteStopDetail(BaseView):
    '''
    A Stop's details for a specific Route
    '''

    def get_data(self, request, region, agency, route, pk):
        agency = get_object_or_404(Agency, pk=agency)
        future = get_provider(agency.provider).stop(agency.id, route, pk)
        return future.result().stop
