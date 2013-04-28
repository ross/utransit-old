#
#
#

from django import forms
from django.contrib import admin
from rest_framework.authtoken.models import Token
from www.info.models import Agency, Region, Route


class RegionAdmin(admin.ModelAdmin):
    fields = ('id', 'name', 'sign')
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    model = Region
    search_fields = ('=id', 'name')


admin.site.register(Region, RegionAdmin)


class AgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    model = Agency
    search_fields = ('=region__id', 'id', 'name')


admin.site.register(Agency, AgencyAdmin)


class RouteAdmin(admin.ModelAdmin):
    list_display = ('id', 'agency', 'name')
    model = Route
    search_fields = ('=agency__id', 'id', 'name')


admin.site.register(Route, RouteAdmin)
