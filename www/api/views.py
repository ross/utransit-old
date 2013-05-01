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
from www.info.models import Agency, Direction, Prediction, Region, Route, Stop


class NoParsesMixin(object):

    def metadata(self, request):
        data = super(NoParsesMixin, self).metadata(request)
        # remove parses since we're read-only
        del data['parses']
        return data


class BaseView(NoParsesMixin, APIView):

    def get(self, request, *args, **kwargs):
        return Response(self.get_data(request, *args, **kwargs))


## Root

def api_root(request):
    return HttpResponseRedirect(reverse('regions-list', request=request))


## Regions

class RegionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Region


class RegionList(NoParsesMixin, generics.ListAPIView):
    '''
    A list of Regions
    '''
    model = Region
    serializer_class = RegionSerializer

## Region

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

## Agency

class RouteSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')

    class Meta:
        exclude = ('agency', 'order')
        model = Route


class AgencyDetailSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    routes = RouteSerializer(many=True)

    class Meta:
        exclude = ('provider',)
        model = Agency


class AgencyDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    An Agency's details
    '''
    model = Agency
    serializer_class = AgencyDetailSerializer

    def retrieve(self, request, region, pk):
        self.object = get_object_or_404(Agency,
                                        pk=Agency.create_id(region, pk))
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)

## Route

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
    directions = DirectionSerializer(many=True)
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

    def retrieve(self, request, region, agency, pk):
        agency = Agency.create_id(region, agency)
        self.object = get_object_or_404(Route, pk=Route.create_id(agency, pk))
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)

## Stop

class PredictionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prediction

class StopDetailSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    predictions = PredictionSerializer(many=True, source='get_predictions')

    class Meta:
        exclude = ('agency',)
        model = Stop


class RouteStopDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A Stop's details for a specific Route
    '''
    model = Stop
    serializer_class = StopDetailSerializer

    def retrieve(self, request, region, agency, route, pk):
        agency = Agency.create_id(region, agency)
        self.object = get_object_or_404(Stop, pk=Stop.create_id(agency, pk))
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)
