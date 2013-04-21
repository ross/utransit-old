#
#
#

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.renderers import BrowsableAPIRenderer
from www.api.clients import get_provider
from www.api.models import Agency, Region
from www.api.renderers import JSONRenderer


class BaseView(APIView):
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def metadata(self, request):
        data = super(BaseView, self).metadata(request)
        # remove parses since we're read-only
        del data['parses']
        return data

    def get(self, request, *args, **kwargs):
        return Response(self.get_data(request, *args, **kwargs))


def api_root(request):
    return HttpResponseRedirect(reverse('regions-list', request=request))


class RegionList(BaseView):
    '''
    A list of Regions
    '''


    def get_data(self, request):
        return Region.objects.all()


class RegionDetail(BaseView):
    '''
    A Region's details
    '''

    def get_data(self, request, pk):
        region = get_object_or_404(Region, pk=pk)
        return region.data


class AgencyDetail(BaseView):
    '''
    An Agency's details
    '''

    def get_data(self, request, region, pk):
        agency = get_object_or_404(Agency, pk=pk)
        future = get_provider(agency.provider).routes(pk)
        data = agency.data
        data['routes'] = future.result().routes
        return data


class RouteDetail(BaseView):
    '''
    A Route's details
    '''

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
