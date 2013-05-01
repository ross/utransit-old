#
#
#

from requests import Session as Session
from time import sleep
import re

digit_re = re.compile(r'^(\d+)(.*)')


def route_key(r):
    key = r.sign
    match = digit_re.match(key)
    if match:
        return 'zzz{0:08d}{1}'.format(int(match.group(1)), match.group(2))
    else:
        return key


class RateLimitedSession(Session):

    def request(self, *args, **kwargs):
        ret = super(RateLimitedSession, self).request(*args, **kwargs)
        # TODO: "better" way of rate limiting
        sleep(0.5)
        return ret
