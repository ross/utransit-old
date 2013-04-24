#
#
#

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

class APIKeyAuthentication(TokenAuthentication):

    def authenticate(self, request):

        token = request.GET.get('token', None)
        if token:
            ret = self.authenticate_credentials(token)
        else:
            ret = super(APIKeyAuthentication, self).authenticate(request)

        if not ret and not settings.DEBUG:
            raise exceptions.AuthenticationFailed('Token required')
        return ret
