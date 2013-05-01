#
#
#

from django import forms
from django.contrib import admin
from rest_framework.authtoken.models import Token
from www.info.models import Agency, Direction, Region, Route, Stop, \
    StopDirection


class RegionAdmin(admin.ModelAdmin):
    fields = ('id', 'name', 'sign')
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    model = Region
    search_fields = ('=id', 'name')
    # TODO: static list of agencies


admin.site.register(Region, RegionAdmin)


class AgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    model = Agency
    search_fields = ('=region__id', 'id', 'name')
    # TODO: static list of routes


admin.site.register(Agency, AgencyAdmin)


class RouteAdmin(admin.ModelAdmin):
    list_display = ('id', 'agency', 'name')
    model = Route
    ordering = ('agency', 'order')
    search_fields = ('=agency__id', 'id', 'name')
    # TODO: static list of directions


admin.site.register(Route, RouteAdmin)


class DirectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'route', 'name')
    model = Direction
    search_fields = ('=route__id', 'id', 'name')
    # TODO: static list of stops


admin.site.register(Direction, DirectionAdmin)


class StopAdmin(admin.ModelAdmin):
    list_display = ('id', 'agency', 'name')
    model = Stop
    search_fields = ('=agency__id', 'id', 'name')
    # TODO: static list of routes


admin.site.register(Stop, StopAdmin)
