#
#
#

from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

class APIKeyAuthentication(TokenAuthentication):

    def authenticate(self, request):
        token = request.GET.get('token', None)

        if not token:
            ret = super(APIKeyAuthentication, self).authenticate(request)
            if not ret:
                raise exceptions.AuthenticationFailed('Token required')


        return self.authenticate_credentials(token)
