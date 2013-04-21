#
#
#

from django.contrib import admin
from www.api.models import Agency, Region


class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    model = Region
    search_fields = ('=id', 'name')


admin.site.register(Region, RegionAdmin)


class AgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    model = Agency
    search_fields = ('=region__id', 'id', 'name')


admin.site.register(Agency, AgencyAdmin)
