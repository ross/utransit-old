#
#
#

from .bart import Bart
from .gtfs import Gtfs
from .nextbus import NextBus
from .onebusaway import OneBusAway

def get_provider(id):
    if id == 'OneBusAway':
        return OneBusAway()
    elif id == 'NextBus':
        return NextBus()
    elif id == 'Bart':
        return Bart()
    elif id == 'GTFS':
        return Gtfs()
    raise Exception('unknown provider')
