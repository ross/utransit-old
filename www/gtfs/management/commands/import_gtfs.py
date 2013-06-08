#
#
#

from __future__ import absolute_import

from csv import DictReader
from django.core.management.base import BaseCommand
from django.db import transaction
from os.path import isfile, join
from pprint import pprint
from www.gtfs.models import Agency, Calendar, CalendarDate, FareAttribute, \
    FareRule, FeedInfo, Frequency, Route, Shape, Shape, Stop, StopTime, Trip, \
    Transfer
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = '<gtfs_dir>'
    help = 'Imports a gtfs data feed'

    def handle(self, directory, *args, **options):
        transaction.enter_transaction_management()
        transaction.managed()

        logger.info('importing %s', directory)

        # TODO: cleanout any existing information

        with open(join(directory, 'agency.txt'), 'r') as fh:
            for agency in DictReader(fh):
                Agency(**{k.replace('agency_', ''): v
                          for k, v in agency.items()}).save()

        with open(join(directory, 'stops.txt'), 'r') as fh:
            for stop in DictReader(fh):
                Stop(**{k.replace('stop_', ''): v
                        for k, v in stop.items()}).save()

        with open(join(directory, 'routes.txt'), 'r') as fh:
            for route in DictReader(fh):
                Route(**{k.replace('route_', ''): v
                         for k, v in route.items()}).save()

        with open(join(directory, 'calendar.txt'), 'r') as fh:
            for calendar in DictReader(fh):
                Calendar(**calendar).save()

        with open(join(directory, 'calendar_dates.txt'), 'r') as fh:
            for calendar_date in DictReader(fh):
                CalendarDate(**calendar_date).save()

        with open(join(directory, 'shapes.txt'), 'r') as fh:
            for shape in DictReader(fh):
                Shape(**{k.replace('shape_', ''): v
                         for k, v in shape.items()}).save()

        with open(join(directory, 'trips.txt'), 'r') as fh:
            for trip in DictReader(fh):
                if trip.get('shape_id', None) == '':
                    trip['shape_id'] = None
                if trip.get('block_id', None) == '':
                    trip['block_id'] = None
                if trip.get('direction_id', None) == '':
                    trip['direction_id'] = None
                Trip(**{k.replace('trip_', ''): v
                        for k, v in trip.items()}).save()

        with open(join(directory, 'stop_times.txt'), 'r') as fh:
            for stop_time in DictReader(fh):
                if stop_time.get('drop_off_type', None) == '':
                    stop_time['drop_off_type'] = None
                if stop_time.get('pickup_type', None) == '':
                    stop_time['pickup_type'] = None
                StopTime(**stop_time).save()

        with open(join(directory, 'fare_attributes.txt'), 'r') as fh:
            for fare_attribute in DictReader(fh):
                # non-standard, in BART
                fare_attribute.pop('agency_id')
                if fare_attribute.get('transfers', None) == '':
                    fare_attribute['transfers'] = None
                if fare_attribute.get('transfer_duration', None) == '':
                    fare_attribute['transfer_duration'] = None
                FareAttribute(**{k.replace('fare_', ''): v
                                 for k, v in fare_attribute.items()}).save()

        with open(join(directory, 'fare_rules.txt'), 'r') as fh:
            for fare_rule in DictReader(fh):
                FareRule(**fare_rule).save()

        with open(join(directory, 'shapes.txt'), 'r') as fh:
            for shape in DictReader(fh):
                Shape(**{k.replace('shape_', ''): v
                         for k, v in shape.items()}).save()

        with open(join(directory, 'frequencies.txt'), 'r') as fh:
            for frequency in DictReader(fh):
                Frequency(**frequency).save()

        with open(join(directory, 'transfers.txt'), 'r') as fh:
            for transfer in DictReader(fh):
                Transfer(**{k.replace('transfer_', ''): v
                            for k, v in transfer.items()}).save()

        with open(join(directory, 'feed_info.txt'), 'r') as fh:
            for feed_info in DictReader(fh):
                FeedInfo(**{k.replace('feed_', ''): v
                            for k, v in feed_info.items()}).save()

        transaction.commit()

        transaction.leave_transaction_management()
        logger.info('done with %s', directory)
