#
#
#

from django.contrib import admin
from www.api.models import Region


class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    model = Region
    search_fields = ('=id', 'name')


admin.site.register(Region, RegionAdmin)
