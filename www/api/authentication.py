#
#
#

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

class TokenMiddlewareAuthentication(BaseAuthentication):

    def authenticate(self, request):
        return request.token_user()

    def authenticate_header(self, request):
        return 'Token'
