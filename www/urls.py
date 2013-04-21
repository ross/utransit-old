from django.conf.urls import patterns, include, url
from www.api.views import AgencyDetail, ApiRoot, RegionDetail, RegionList

# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'www.views.home', name='home'),
    # url(r'^www/', include('www.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('www.api.views',
                        url(r'^api/$', ApiRoot.as_view(), name='api_root'),
                        url(r'^api/regions/$', RegionList.as_view(),
                            name='regions-list'),
                        url(r'^api/regions/(?P<id>[\w-]+)/$',
                            RegionDetail.as_view(), name='region-detail'),
                        url(r'^api/regions/(?P<region>[\w-]+)'
                            r'/agencies/(?P<id>[\w-]+)/$',
                            AgencyDetail.as_view(), name='agency-detail'))
