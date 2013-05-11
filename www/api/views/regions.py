#
#
#

from rest_framework import generics, serializers
from www.info.models import Region
from .mixins import NoParsesMixin
from ..serializers import AgencySerializer, RegionSerializer


class RegionList(NoParsesMixin, generics.ListAPIView):
    '''
    A list of Regions
    '''
    model = Region
    serializer_class = RegionSerializer


class RegionDetailSerializer(RegionSerializer):
    agencies = AgencySerializer(many=True)

    class Meta(RegionSerializer.Meta):
        pass


class RegionDetail(NoParsesMixin, generics.RetrieveAPIView):
    '''
    A Region's details
    '''
    model = Region
    serializer_class = RegionDetailSerializer
