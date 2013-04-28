#
#
#

from rest_framework.authentication import get_authorization_header
from django.contrib.auth import get_user_model


User = get_user_model()


def get_user_by_token(request):
    token_user = getattr(request, '_token_user', None)
    if token_user:
        return token_user

    token = request.GET.get('token', None)
    if not token:
        auth = get_authorization_header(request).split()
        if auth and auth[0].lower() == b'token' and len(auth) == 2:
            token = auth[1]
    if token:
        try:
            request._token_user = \
                (User.objects.get(auth_token__key=token), token)
            return request._token_user
        except User.DoesNotExist:
            pass
    return None


class TokenMiddleware:

    def process_request(self, request):
        # using lambda to make it lazy
        request.token_user = lambda: get_user_by_token(request)
