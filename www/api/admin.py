#
#
#

from django import forms
from django.contrib import admin
from rest_framework.authtoken.models import Token
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


class TokenAdmin(admin.ModelAdmin):
    list_display = ('user',)
    model = Token
    readonly_fields = ('key',)
    search_fields = ('=key', 'user__username')

admin.site.register(Token, TokenAdmin)
