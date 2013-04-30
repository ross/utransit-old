#
#
#

from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option
from pprint import pprint
from www.gtfs.loader import GTFSLoader
from www.info.models import Agency, Direction, Region, Route, Stop, \
    StopDirection, route_types, stop_types
import logging
import re


logger = logging.getLogger(__name__)
digit_re = re.compile(r'^(\d+)(.*)')


def _route_key(r):
    key = r.route_short_name
    match = digit_re.match(key)
    if match:
        return 'zzz{0:08d}{1}'.format(int(match.group(1)), match.group(2))
    else:
        return key



class Command(BaseCommand):
    args = '<region> <directory>'
    help = 'Imports/updates data via a GTFS dataset'
    #option_list = BaseCommand.option_list + (make_option('--lenient', '-l',
    #                                                     action='store_true',
    #                                                     default=False),
    #                                         make_option('--web', '-w',
    #                                                     action='store_true',
    #                                                     default=False))

    @transaction.commit_manually
    def handle(self, region, directory, *args, **options):
        try:
            self.run(region, directory)
            transaction.commit()
        finally:
            transaction.rollback()

    def run(self, region, directory):
        loader = GTFSLoader(directory)

        logger.debug('processing stops')
        stops = {s.stop_id: s for s in loader.stops}
        logger.debug('processing trips')
        trips = {}
        for stop_time in loader.stop_times:
            trips.setdefault(stop_time.trip_id, []).append(stop_time.stop_id)

        region = Region.objects.get(id=region)

        logger.debug('processing agencies')
        for a in loader.agencies:
            aid = Agency.create_id(region.id, a.agency_id.lower())
            logger.info('%8s: %s', aid, a.agency_name)

            agency, created = Agency.objects \
                .get_or_create(region=region, id=aid)
            if created:
                # only set the sign on new objects, in case it has been edited
                # after the fact
                agency = Agency(region=region, id=aid, sign=a.id.upper())
            agency.name = a.agency_name
            agency.url = a.agency_url
            agency.timezone = a.agency_timezone
            agency.lang = a.agency_lang
            agency.phone = getattr(a, 'agency_phone', None)
            agency.fare_url = getattr(a, 'fare_url', None)
            agency.provider = 'GTFS'
            agency.save()

            # only routes for this agency, sorted with "magic"
            if hasattr(list(loader.routes)[0], 'agency_id'):
                routes = filter(lambda c: c.agency_id == a.agency_id,
                                loader.routes)
            else:
                # if there's no agency_id, we'll assume they're all a part of 
                # the single agency we're processing, hopefully that's correct
                routes = loader.routes
            routes = sorted(routes, key=_route_key)


            for i, r in enumerate(routes):
                rid = Route.create_id(aid, r.route_id.lower())
                logger.info('  %12s: %s', rid, r.route_short_name)

                defaults = {'order': i}
                route, created = Route.objects.get_or_create(agency=agency,
                                                             id=rid,
                                                             defaults=defaults)
                route.name = r.route_long_name
                route.sign = r.route_short_name
                route.type = route_types[int(r.route_type)]
                route.url = getattr(r, 'route_url', None)
                route_color = getattr(r, 'route_color', None)
                if route_color:
                    route.color = route_color
                else:
                    route.color = None
                route.order = i
                route.save()

                directions = {}
                trip_names = {}
                for i, t in enumerate(
                    filter(lambda c: c.route_id == r.route_id, loader.trips)):
                    directions.setdefault(t.direction_id, []) \
                            .append(trips[t.trip_id])
                    trip_names.setdefault(t.direction_id, []) \
                            .append(t.trip_headsign)

                for d, ts in directions.items():
                    did = Direction.create_id(route.id, str(d))
                    logger.info('    %12s: ', did)

                    direction, created = \
                        Direction.objects.get_or_create(route=route,
                                                        id=did)
                    direction.name = trip_names[d][0]
                    direction.save()

                    for i, s in enumerate(max(ts, key=len)):
                        s = stops[s]
                        sid = Stop.create_id(aid, s.stop_id.lower())
                        logger.info('      %12s: %s', sid, s.stop_name)

                        defaults = {'lat': s.stop_lat, 'lon': s.stop_lon}
                        stop, created = \
                            Stop.objects.get_or_create(agency=agency,
                                                       id=sid,
                                                       defaults=defaults)
                        stop.name = s.stop_name
                        stop_code = getattr(s, 'stop_code', None)
                        if stop_code:
                            stop.code = stop_code
                        else:
                            stop.code = None
                        stop_type = getattr(s, 'stop_type', None)
                        if stop_type:
                            stop.type = stop_types[int(stop_type)]
                        else:
                            stop.type = None
                        stop.lat = s.stop_lat
                        stop.lon = s.stop_lon
                        stop.save()

                        defaults = {'order': i}
                        stop_direction, created = StopDirection.objects \
                            .get_or_create(stop=stop, direction=direction,
                                           defaults=defaults)
                        if stop_direction.order != i:
                            stop_direction.order = i
                            stop_direction.save()

