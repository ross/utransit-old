from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.decorators.cache import cache_page
from www.api.views import AgencyDetail, RegionDetail, RegionList, \
    RouteDetail, RouteStopDetail

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^adm/', include(admin.site.urls)),
)

urlpatterns += patterns('www.api.views',
                        url(r'^api/$', 'api_root', name='api_root'),
                        url(r'^api/regions/$',
                            cache_page(RegionList.as_view(), 60 * 60),
                            name='regions-list'),
                        url(r'^api/regions/(?P<pk>[\w-]+)/$',
                            cache_page(RegionDetail.as_view(), 60 * 60),
                            name='region-detail'),
                        url(r'^api/regions/(?P<region>[\w-]+)'
                            r'/agencies/(?P<pk>[\w-]+)/$',
                            cache_page(AgencyDetail.as_view(), 60 * 60),
                            name='agency-detail'),
                        url(r'^api/regions/(?P<region>[\w-]+)'
                            r'/agencies/(?P<agency>[\w-]+)'
                            r'/routes/(?P<pk>[\w-]+)/$',
                            cache_page(RouteDetail.as_view(), 60 * 5),
                            name='route-detail'),
                        url(r'^api/regions/(?P<region>[\w-]+)'
                            r'/agencies/(?P<agency>[\w-]+)'
                            r'/routes/(?P<route>[\w-]+)'
                            r'/stops/(?P<pk>[\w-]+)/$',
                            RouteStopDetail.as_view(), name='stop-detail'))
