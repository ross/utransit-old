#
#
#

from collections import defaultdict
from django.db.models.query import prefetch_related_objects
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from www.clients import get_provider
from www.info.models import Agency, Arrival, Direction, Region, Route, Stop

# TODO:
#  - rework hierarchy to make sense. have base serializers for all of the
#  objects with meta get_id, meta to exclude etc. that way objects will be
#  consistent. then in specific views we can inherit to add extra fields for
#  context, a la arrivals
#  - get naming in order

class NoParsesMixin(object):

    def metadata(self, request):
        data = super(NoParsesMixin, self).metadata(request)
        # remove parses since we're read-only
        del data['parses']
        return data


class BaseView(NoParsesMixin, APIView):

    def get(self, request, *args, **kwargs):
        return Response(self.get_data(request, *args, **kwargs))


class HRefField(serializers.Field):

    def __init__(self, *args, **kwargs):
        super(HRefField, self).__init__(*args, **kwargs)
        kwargs['read_only'] = True

    def field_to_native(self, obj, field_name):
        if field_name == 'href':
            href = obj.get_absolute_url()
            return self.context['request'].build_absolute_uri(href)
        return super(HRefField, self).field_to_native(obj, field_name)


## Root

def api_root(request):
    return HttpResponseRedirect(reverse('regions-list', request=request))


## Regions

class RegionSerializer(serializers.ModelSerializer):
    href = HRefField()

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
    href = HRefField()

    class Meta:
        exclude = ('provider', 'region')
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
    href = HRefField()

    class Meta:
        exclude = ('agency', 'order')
        model = Route


class AgencyDetailSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    region = RegionSerializer()
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
    id = serializers.Field(source='get_id')
    stops = serializers.Field(source='get_stop_ids')

    class Meta:
        exclude = ('route',)
        model = Direction


class RouteStopSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')

    def field_to_native(self, obj, field_name):
        if field_name == 'stops':
            value = getattr(obj, self.source)
            return {v.get_id(): self.to_native(v) for v in value()}
        return super(RouteStopSerializer, self).field_to_native(obj,
                                                                field_name)

    def to_native(self, obj):
        # since we have to add a route in to get a route specific stop
        # we need to manually compute and add the href
        ret = super(RouteStopSerializer, self).to_native(obj)
        href = obj.get_absolute_url(self.context['route_slug'])
        ret['href'] = self.context['request'].build_absolute_uri(href)
        return ret

    class Meta:
        exclude = ('agency',)
        model = Stop


class AgencyRegionSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    href = HRefField()
    region = RegionSerializer()

    class Meta:
        exclude = ('provider',)
        model = Agency


class RouteDetailSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    directions = DirectionSerializer(many=True)
    stops = RouteStopSerializer(many=True, source='get_stops')
    agency = AgencyRegionSerializer()

    class Meta:
        exclude = ('order',)
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
        try:
            self.object = Route.objects.select_related('agency',
                                                       'agency__region') \
                .prefetch_related('directions', 'directions__stops') \
                .get(pk=Route.create_id(Agency.create_id(region, agency), pk))
        except Route.DoesNotExist:
            raise Http404('No Route matches the given query.')
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)


## Route Stop

class RouteStopArrivalSerializer(serializers.ModelSerializer):
    destination = serializers.Field(source='destination.get_id')

    class Meta:
        exclude = ('id', 'route', 'stop', 'direction')
        model = Arrival


class RouteStopStopSerializer(serializers.ModelSerializer):

    # TODO: can this be turned in to a mix-in, it's repeated
    def field_to_native(self, obj, field_name):
        if field_name == 'stops':
            value = getattr(obj, self.source)
            return {v.get_id(): self.to_native(v) for v in value()}
        return super(RouteStopSerializer, self).field_to_native(obj,
                                                                field_name)

    class Meta:
        model = Stop


class RouteStopSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    agency = AgencyRegionSerializer()
    arrivals = RouteStopArrivalSerializer(many=True, source='get_arrivals')
    stops = RouteStopStopSerializer(many=True, source='get_stops')
    # TODO: other routes

    class Meta:
        model = Stop


class RouteStopDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A Stop's details for a specific Route
    '''
    model = Stop
    serializer_class = RouteStopSerializer

    def retrieve(self, request, region, agency, route, pk):
        try:
            stop = Stop.objects.select_related('agency', 'agency__region') \
                .get(pk=Stop.create_id(Agency.create_id(region, agency), pk))
        except Stop.DoesNotExist:
            raise Http404('No Route matches the given query.')
        agency = stop.agency
        route = get_object_or_404(Route, pk=Route.create_id(agency.id, route))
        stop._arrivals = get_provider(stop.agency).arrivals(stop, route)
        self.object = stop
        serializer = self.get_serializer(stop)
        return Response(serializer.data)


## Agency Stop

class AgencyStopArrivalSerializer(serializers.ModelSerializer):
    direction = serializers.Field(source='direction.get_id')
    destination = serializers.Field(source='destination.get_id')
    route = serializers.Field(source='direction.route.get_id')

    class Meta:
        exclude = ('id', 'stop',)
        model = Arrival


class AgencyStopDirectionSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')

    def field_to_native(self, obj, field_name):
        if field_name == 'directions':
            value = getattr(obj, field_name)
            return {d.get_id(): self.to_native(d) for d in value.all()}
        return super(AgencyStopDirectionSerializer, self) \
            .field_to_native(obj, field_name)

    class Meta:
        exclude = ('route', 'stops')
        model = Direction


class AgencyStopRouteSerializer(serializers.ModelSerializer):
    directions = AgencyStopDirectionSerializer(many=True)
    href = HRefField()

    def field_to_native(self, obj, field_name):
        if field_name == 'routes':
            value = getattr(obj, '_routes')
            return {r.get_id(): self.to_native(r) for r in value}
        return super(AgencyStopRouteSerializer, self) \
            .field_to_native(obj, field_name)

    class Meta:
        model = Route


class AgencyStopSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    arrivals = AgencyStopArrivalSerializer(many=True, source='get_arrivals')
    stops = RouteStopStopSerializer(many=True, source='get_stops')
    routes = AgencyStopRouteSerializer(many=True,
                                       source='get_routes')

    class Meta:
        model = Stop


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
        prefetch_related_objects(arrivals, ['direction__route__directions'])
        stop._arrivals = arrivals

        routes = {}
        for arrival in arrivals:
            if arrival.direction:
                route = arrival.direction.route
                routes[route.id] = route
        stop._routes = routes.values()

        self.object = stop
        serializer = self.get_serializer(stop)
        return Response(serializer.data)


## Nearby

class NearbyDirectionSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    route = serializers.Field(source='route.get_id')

    class Meta:
        exclude = ('stops',)
        model = Direction


class NearbyStopSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    agency = serializers.Field(source='agency.get_id')
    region = serializers.Field(source='agency.region.id')
    directions = NearbyDirectionSerializer(many=True)
    distance = serializers.Field()
    # TODO: routes

    def to_native(self, obj):
        # we need to manually compute and add the href
        ret = super(NearbyStopSerializer, self).to_native(obj)
        href = obj.get_absolute_url()
        ret['href'] = self.context['request'].build_absolute_uri(href)
        return ret

    class Meta:
        model = Stop


class NearbyRegionSerializer(serializers.ModelSerializer):
    href = HRefField()

    def field_to_native(self, obj, field_name):
        if field_name == 'regions':
            value = getattr(obj, field_name)
            return {v.id: self.to_native(v) for v in value()}
        return super(NearbyRegionSerializer, self).field_to_native(obj,
                                                                   field_name)

    class Meta:
        model = Region


class NearbyAgencySerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    href = HRefField()

    def field_to_native(self, obj, field_name):
        if field_name == 'agencies':
            value = getattr(obj, field_name)
            agencies = defaultdict(dict)
            for v in value():
                agencies[v.region_id][v.get_id()] = self.to_native(v)
            return agencies
        return super(NearbyAgencySerializer, self).field_to_native(obj,
                                                                   field_name)

    class Meta:
        model = Agency


class NearbyRouteSerializer(serializers.ModelSerializer):
    id = serializers.Field(source='get_id')
    href = HRefField()

    def field_to_native(self, obj, field_name):
        if field_name == 'routes':
            value = getattr(obj, field_name)
            routes = defaultdict(lambda: defaultdict(dict))
            for v in value():
                region_id = Route.get_region_id(v.id)
                agency_id = Route.get_agency_id(v.id)
                routes[region_id][agency_id][v.get_id()] = self.to_native(v)
            return routes
        return super(NearbyAgencySerializer, self).field_to_native(obj,
                                                                   field_name)

    class Meta:
        model = Route


class NearbySerializer(serializers.Serializer):
    stops = NearbyStopSerializer(many=True)
    regions = NearbyRegionSerializer(many=True)
    agencies = NearbyAgencySerializer(many=True)
    routes = NearbyRouteSerializer(many=True)


class NearbyDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A list of nearby Stops
    '''
    model = Stop
    serializer_class = NearbySerializer

    def regions(self):
        return [s.agency.region for s in self.stops]

    def agencies(self):
        return [s.agency for s in self.stops]

    def routes(self):
        routes = {}
        for stop in self.stops:
            for direction in stop.directions.all():
                route = direction.route
                routes[route.id] = direction.route

        return routes.values()

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

        # we'll use ourselves as the object, listing it to prevent running the
        # query twice
        stops = list(Stop.objects.nearby(lat, lon, radius))

        if region and agency:
            agency_id = Agency.create_id(region, agency)
            print('\n\n%s\n\n' % agency_id)

            def desired_agency(stop):
                return stop.agency_id == agency_id

            stops = filter(desired_agency, stops)

        prefetch_related_objects(stops, ['agency', 'agency__region',
                                         'directions', 'directions__route'])

        self.stops = stops
        self.object = self

        serializer = self.get_serializer(self.object)
        return Response(serializer.data)
