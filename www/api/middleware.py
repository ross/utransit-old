#
#
#

from django.contrib.auth import get_user_model


User = get_user_model()


def get_user_by_token(request):
    token_user = getattr(request, '_token_user', None)
    if token_user:
        return token_user

    token = request.GET.get('token', None)
    if not token:
        auth = request.META.get('HTTP_AUTHORIZATION', b'')
        if type(auth) == type(''):
            # Work around django test client oddness
            auth = auth.encode(HTTP_HEADER_ENCODING)
        auth = auth.split()
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
