#
#
#

from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.response import Response
from www.info.models import Agency
from .mixins import NoParsesMixin
from ..serializers import AgencySerializer, RegionSerializer, RouteSerializer


class AgencyDetailSerializer(AgencySerializer):
    id = serializers.Field(source='get_id')
    region = RegionSerializer()
    routes = RouteSerializer(many=True)

    class Meta(AgencySerializer.Meta):
        exclude = AgencySerializer.Meta.exclude - {'region',}


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
