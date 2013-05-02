from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.utils.decorators import available_attrs
from django.views.decorators.cache import cache_page
from functools import wraps
from www.api.views import AgencyDetail, NearbyStopList, RegionDetail, \
    RegionList, RouteDetail, RouteStopDetail

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^adm/', include(admin.site.urls)),
)


# http://stackoverflow.com/questions/11661503/django-caching-for-authenticated-users-only
def cache_on_auth(timeout):
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated() or request.token_user():
                return cache_page(timeout)(view_func)(request, *args, **kwargs)
            else:
                return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


urlpatterns += patterns('www.api.views',
                        url(r'^api/$', 'api_root', name='api_root'),
                        url(r'^api/regions/$',
                            cache_on_auth(60 * 60)(RegionList.as_view()),
                            name='regions-list'),
                        url(r'^api/regions/(?P<pk>[\w-]+)/$',
                            cache_on_auth(60 * 60)(RegionDetail.as_view()),
                            name='region-detail'),
                        url(r'^api/regions/(?P<region>[\w-]+)'
                            r'/agencies/(?P<pk>[\w-]+)/$',
                            cache_on_auth(60 * 60)(AgencyDetail.as_view()),
                            name='agency-detail'),
                        url(r'^api/regions/(?P<region>[\w-]+)'
                            r'/agencies/(?P<agency>[\w-]+)'
                            r'/routes/(?P<pk>[\w-]+)/$',
                            cache_on_auth(60 * 5)(RouteDetail.as_view()),
                            name='route-detail'),
                        url(r'^api/regions/(?P<region>[\w-]+)'
                            r'/agencies/(?P<agency>[\w-]+)'
                            r'/routes/(?P<route>[\w-]+)'
                            r'/stops/(?P<pk>[\w-]+)/$',
                            RouteStopDetail.as_view(), name='stop-detail'),

                        url(r'^api/nearby/',
                            NearbyStopList.as_view(), name='nearby-list'))

urlpatterns += patterns('', url(r'^api-auth/',
                                include('rest_framework.urls',
                                        namespace='rest_framework')))
