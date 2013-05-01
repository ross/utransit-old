#
#
#

from django.db import transaction
from www.info.models import Direction, Route, Stop, StopDirection
from .bart import Bart
from .gtfs import Gtfs
from .nextbus import NextBus
from .onebusaway import OneBusAway
import logging

logger = logging.getLogger(__name__)


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


@transaction.commit_manually
def sync_agency(agency):
    try:
        _sync_agency(agency)
        transaction.commit()
    finally:
        transaction.rollback()

def _sync_agency(agency):
    provider = get_provider(agency.provider)

    existing_routes = {r.id for r in agency.routes.all()}
    logger.info('agency.id=%s', agency.id)
    logger.debug('    existing routes=%s', existing_routes)
    all_directions = []
    all_stops = {}
    for route in provider.routes(agency):
        logger.info('    route.id=%s', route.id)
        existing_routes.discard(route.id)
        try:
            existing = Route.objects.get(pk=route.id)
            logger.debug('        existing')
            # update the existing
            if existing.update(route):
                logger.debug('        updated')
                # something changed, save
                existing.save()
            # use the existing object from here on out
            route = existing
        except Route.DoesNotExist:
            logger.debug('        new')
            # create a new one by saving the new one
            route.save()

        directions, stops = provider.stops(route)
        all_stops.update(stops)
        all_directions.append((route, directions))

    for old in existing_routes:
        logger.info('    deleting route.id=%s', old)
        Route.objects.get(pk=old).delete()

    existing_stops = {s.id for s in route.agency.stops.all()}
    logger.debug('    existing stops=%s', existing_stops)
    for stop in all_stops.values():
        logger.info('    stop.id=%s', stop.id)
        existing_stops.discard(stop.id)
        try:
            existing = Stop.objects.get(pk=stop.id)
            logger.debug('        existing')
            if existing.update(stop):
                logger.debug('        updated')
                existing.save()
            # replace with the existing stop
            all_stops[stop.id] = existing
        except Stop.DoesNotExist:
            logger.debug('        new')
            stop.save()

    for old in existing_stops:
        logger.info('    deleting stop.id=%s', old)
        Stop.objects.get(pk=old).delete()

    for route, directions in all_directions:
        existing_directions = {d.id for d in route.directions.all()}
        for direction in directions:
            logger.info('    direction.id=%s', direction.id)
            existing_directions.discard(direction.id)
            try:
                existing = Direction.objects.get(pk=direction.id)
                logger.debug('        existing')
                # manually copy over stop_ids to avoid it causing a false
                # update
                existing.stop_ids = direction.stop_ids
                if existing.update(direction):
                    logger.debug('        updated')
                    existing.save()
                direction = existing
            except Direction.DoesNotExist:
                logger.debug('        new')
                direction.save()

            existing_sids = {ds.stop_id
                             for ds in direction.stop_directions.all()}
            logger.debug('        existing stop.ids=%s', existing_sids)
            for i, stop_id in enumerate(direction.stop_ids):
                logger.info('        stop.id=%s', stop_id)
                existing_sids.discard(stop_id)
                try:
                    existing = StopDirection.objects \
                        .get(direction_id=direction.id, stop_id=stop_id)
                    logger.debug('            existing')
                    if existing.order != i:
                        logger.debug('            updated')
                        existing.order = i
                        existing.save()
                except StopDirection.DoesNotExist:
                    logger.debug('            new')
                    StopDirection(direction_id=direction.id,
                                  stop_id=stop_id, order=i).save()

            for old in existing_sids:
                logger.info('        deleting direction_stop.stop_id=%s',
                            old)
                StopDirection.objects.get(direction_id=direction.id,
                                          stop_id=old).delete()

        for old in existing_directions:
            logger.info('    deleting direction.id=%s', old)
            Direction.objects.get(pk=old).delete()
            # TODO: cascade to StopDirection's
