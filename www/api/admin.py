#
#
#

from django import forms
from django.contrib import admin
from rest_framework.authtoken.models import Token


class TokenAdmin(admin.ModelAdmin):
    list_display = ('user',)
    model = Token
    readonly_fields = ('key',)
    search_fields = ('=key', 'user__username')

admin.site.register(Token, TokenAdmin)
