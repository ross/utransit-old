#
#
#

from django.http import HttpResponseRedirect
from rest_framework.reverse import reverse
from .agencies import AgencyDetail
from .legacy import LegacyNearby
from .nearby import NearbyDetail
from .regions import RegionDetail, RegionList
from .routes import RouteDetail
from .stops import AgencyStopDetail, RouteStopDetail


def api_root(request):
    return HttpResponseRedirect(reverse('regions-list', request=request))
