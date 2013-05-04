#
#
#

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from math import cos, radians
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


class URLField(serializers.Field):

    def __init__(self, *args, **kwargs):
        super(URLField, self).__init__(*args, **kwargs)
        kwargs['read_only'] = True

    def field_to_native(self, obj, field_name):
        if field_name == 'url':
            url = obj.get_absolute_url()
            return self.context['request'].build_absolute_uri(url)
        return super(URLField, self).field_to_native(obj, field_name)

## Root

def api_root(request):
    return HttpResponseRedirect(reverse('regions-list', request=request))


## Regions

class RegionSerializer(serializers.ModelSerializer):
    url = URLField()

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
    url = URLField()

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
    url = URLField()

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

    def to_native(self, obj):
        # since we have to add a route in to get a route specific stop
        # we need to manually compute and add the url
        ret = super(StopSerializer, self).to_native(obj)
        url = obj.get_absolute_url(self.context['route_slug'])
        ret['url'] = self.context['request'].build_absolute_uri(url)
        return ret

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

    def get_serializer_context(self):
        ret = super(RouteDetail, self).get_serializer_context()
        # we need to pass our route id along to the stop serializers
        ret['route_slug'] = self.object.get_id()
        return ret

    def retrieve(self, request, region, agency, pk):
        agency = Agency.create_id(region, agency)
        self.object = get_object_or_404(Route, pk=Route.create_id(agency, pk))
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)

## Route Stop

class PredictionSerializer(serializers.ModelSerializer):

    class Meta:
        exclude = ('id', 'stop',)
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
        route = get_object_or_404(Route, pk=Route.create_id(agency, route))
        stop = get_object_or_404(Stop, pk=Stop.create_id(agency, pk))
        stop._predictions = get_provider(stop.agency).predictions(route, stop)
        self.object = stop
        serializer = self.get_serializer(stop)
        return Response(serializer.data)

## Agency Stop

class AgencyStopDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A Stop's details for a specific Route
    '''
    model = Stop
    serializer_class = StopSerializer

    def retrieve(self, request, region, agency, route, pk):
        agency = Agency.create_id(region, agency)
        stop = get_object_or_404(Stop, pk=Stop.create_id(agency, pk))
        # TODO:
        #stop._predictions = get_provider(stop.agency).predictions(route, stop)
        self.object = stop
        serializer = self.get_serializer(stop)
        return Response(serializer.data)


## Nearby

class NearbyStopSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    agency = serializers.Field(source='agency.get_id')
    region = serializers.Field(source='agency.region.id')
    distance = serializers.Field()

    class Meta:
        model = Stop


class NearbyStopList(NoParsesMixin, generics.ListAPIView):
    '''
    A list of nearby Stops
    '''
    model = Stop
    serializer_class = NearbyStopSerializer

    def list(self, request, *args, **kwargs):
        try:
            lat = float(request.GET['lat'])
            lon = float(request.GET['lon'])
            radius = float(request.GET.get('radius', 500.0))
        except KeyError:
            # TODO: bad request, missing param
            raise
        except ValueError:
            # TODO: bad request, bad param
            raise

        # based on
        # http://www.scribd.com/doc/2569355/Geo-Distance-Search-with-MySQL
        # converted to meters

        # create a square to filter out stops we know are out of consideration
        # to avoid calculating their distances
        r = (radius / 110574.61087757687)
        lat_min = lat - r
        lat_max = lat + r
        r = (radius / abs(cos(radians(lat)) * 110574.61087757687))
        lon_min = lon - r
        lon_max = lon + r

        stops = Stop.objects.raw('''
select * from (select s.*, 6378100 * 2 *
    asin(sqrt(power(sin((%s - abs(lat)) * pi() / 180 / 2),2) +
              cos(%s * pi() / 180) * cos(abs(lat) * pi() / 180) *
              power(sin((%s - lon) * pi() / 180 / 2), 2)))
    as distance from info_stop s
    where lat between %s and %s and lon between %s and %s
    order by distance) i where distance < %s limit 20''',
                                 [lat, lat, lon, lat_min, lat_max,
                                  lon_min, lon_max, radius])

        self.object_list = stops
        serializer = self.get_serializer(self.object_list, many=True)
        return Response(serializer.data)
