#
#
#

from django.db import connection
from pprint import pprint
from .models import Direction, Route, DirectionStop, Scheduled


class CreateRouteInfo(object):

    def run(self, route_id):
        cursor = connection.cursor()
        cursor.execute('''select distinct(t.direction_id)
                       from gtfs_trip t where t.route_id = %s''', route_id)
        for row in cursor:
            Direction(id=Direction.create_id(route_id, row[0]),
                      route_id=route_id).save()

        cursor.execute('''select t.direction_id, s.id,
                       avg(st.stop_sequence) as seq from gtfs_trip t join
                       gtfs_stoptime st on t.id = st.trip_id join
                       gtfs_stop s on st.stop_id = s.id
                       where route_id = %s group by s.id, t.direction_id
                       order by t.direction_id, seq''', route_id)
        for i, row in enumerate(cursor):
            DirectionStop(direction_id=Direction.create_id(route_id, row[0]),
                          stop_id=row[1], sequence=i).save()


class CreateStopArrivals(object):

    def run(self, stop_id, active_service_ids):
        cursor = connection.cursor()

        query = '''select t.id, t.route_id, t.direction_id,
                st.arrival_time, st.departure_time
                from gtfs_stoptime st join
                gtfs_trip t on st.trip_id = t.id
                where st.stop_id = %s and t.service_id in ({0})
                order by st.arrival_time''' \
                .format(', '.join(['%s' for x in active_service_ids]))

        cursor.execute(query, [stop_id] + active_service_ids)

        scheduleds = []
        for row in cursor:
            scheduled = Scheduled(trip_id=row[0],
                                  direction_id=Direction.create_id(row[1],
                                                                   row[2]),
                                  stop_id=stop_id, arrival_time=row[3],
                                  departure_time=row[4])
            scheduleds.append(scheduled)

        for scheduled in scheduleds:
            cursor.execute('''select st.stop_id from gtfs_stoptime st
                           where st.trip_id = %s
                           order by stop_sequence desc limit 1''',
                           scheduled.trip_id)
            scheduled.destination_id = cursor.fetchone()[0]
            scheduled.save()
