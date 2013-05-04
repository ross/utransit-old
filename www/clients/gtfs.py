#
#
#

from collections import defaultdict
from csv import DictReader
from os.path import join
from www.info.models import Direction, Route, Stop, route_types, stop_types
from xmltodict import parse
from .utils import route_key
import requests


class Gtfs(object):

    def __init__(self, agency):
        self.agency = agency

        self._cached_routes = None
        self._cached_trips = None
        self._cached_stops = None
        self._cached_trip_stops = None

    def _routes(self, directory):
        if not self._cached_routes:
            with open(join(directory, 'routes.txt'), 'r') as fh:
                self._cached_routes = list(DictReader(fh))

        return self._cached_routes

    def routes(self):
        routes = []

        agency = self.agency

        aid = agency.get_id()
        for route in self._routes(join('data', agency.id)):
            # if there's no agency_id, we'll assume they're all a part of
            # the single agency we're processing, hopefully that's correct
            if 'agency_id' in route and route['agency_id'] != aid:
                continue
            id = Route.create_id(agency.id, route['route_id'])
            routes.append(Route(agency=agency, id=id,
                                sign=route['route_short_name'],
                                name=route['route_long_name'],
                                type=route_types[int(route['route_type'])],
                                site=route.get('route_url', None),
                                color=route.get('route_color', None)))

        routes.sort(key=route_key)
        for i, route in enumerate(routes):
            route.order = i
        return routes

    def _trips(self, directory):
        if not self._cached_trips:
            with open(join(directory, 'trips.txt'), 'r') as fh:
                self._cached_trips = list(DictReader(fh))

        return self._cached_trips

    def _stops(self, directory):
        if not self._cached_stops:
            with open(join(directory, 'stops.txt'), 'r') as fh:
                self._cached_stops = {s['stop_id']: s for s in DictReader(fh)}

        return self._cached_stops

    def _trip_stops(self, directory):
        if not self._cached_trip_stops:
            trip_stops = defaultdict(list)
            with open(join(directory, 'stop_times.txt'), 'r') as fh:
                for stop_time in DictReader(fh):
                    trip_stops[stop_time['trip_id']] \
                        .append(stop_time['stop_id'])
            self._cached_trip_stops = trip_stops

        return self._cached_trip_stops

    def stops(self, route):
        directions = defaultdict(list)
        trip_names = defaultdict(list)
        rid = route.get_id()

        directory = join('data', route.agency.id)

        trip_stops = self._trip_stops(directory)
        direction_stops = defaultdict(list)
        trips = filter(lambda c: rid == c['route_id'], self._trips(directory))
        for i, t in enumerate(trips):
            tid = t['direction_id']
            direction_stops[tid].append(trip_stops[t['trip_id']])
            trip_names[tid].append(t['trip_headsign'])

        all_stops = self._stops(directory)
        directions = []
        stops = {}
        for d, ts in direction_stops.items():
            did = Direction.create_id(route.id, str(d))
            # TODO: pick the most common name?
            direction = Direction(route=route, id=did,
                                  name=trip_names[d][0])

            # pick the largest set of stops, hopefully that'll cover everything
            stop_ids = []
            for sid in max(ts, key=len):
                stop = all_stops[sid]
                sid = Stop.create_id(route.agency.id, sid)
                stop_type = stop.get('location_type', None)
                if stop_type:
                    stop_type = stop_types[int(stop_type)]
                stop = Stop(agency=route.agency, id=sid,
                            name=stop['stop_name'], lat=stop['stop_lat'],
                            lon=stop['stop_lon'], type=stop_type,
                            code=stop.get('code', None))

                stop_ids.append(stop.id)
                stops[stop.id] = stop

            direction.stop_ids = stop_ids
            directions.append(direction)

        return (directions, stops)

    def _lextran_predictions(self, route, stop):
        url = 'http://realtime.lextran.com/InfoPoint/map/GetStopHtml.ashx'
        params = {'stopId': 43}
        headers = {}
        {
            'Accept': '*/*',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': 'ASP.NET_SessionId=mpdeklznzcn5gzqmo2kks155; pyrocms=8l1nivPHBU5k7ABEoD%2FYQhQsfk%2BDHnct5NLFM0QgJJrfSNgfbjIethvsHMpmj9NZZgzepjCI63I5Nm8I5AYp%2BoVJKL%2BcpCRNWediMJ4AjMa4LhfGsbiIrA3NbsYUphKdpcj24SlKNar7tsYb1ufDnUBnAriRA5%2FUuRGy4E0oJDQL1h7seruFUhZjb8GVoJ0WUeZP3n8uBrWTy8xNNRSpyVB2z5KtsuJQ739eGrSRHq1KpSglj3fR5VKpRwIWFMXA%2F4NZf17ruzsJ6H0zrgzWBaECYCVHlFcTxJ%2FIcJaP1rrucRs2TeOfs4DGX%2FV1X%2FmvTrwIXIZpXwJwWNolc9TmgQ%3D%3D; __utma=92861568.1144423841.1367201976.1367201976.1367446315.2; __utmb=92861568.2.10.1367446315; __utmc=92861568; __utmz=92861568.1367201976.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided)',
            'Host': 'realtime.lextran.com',
            'Referer': 'http://realtime.lextran.com/InfoPoint/',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31'
        }
        resp = requests.get(url, params=params, headers=headers)

        with open('/tmp/run.html', 'wb') as fh:
            fh.write(resp.content)
        from pprint import pprint
        pprint(resp.content)
        #data = parse(resp.content)
        #pprint(data)

        return []

    def _translink_predictions(self, route, stop):
        print('\n\n%s\n\n' % stop.get_id())
        url = 'http://api.translink.ca/rttiapi/v1/stops/{0}/estimates' \
            .format(stop.get_id())
        params = {'apiKey': 'AdByQ5Tv82YRhPWOcEHV',
                  'timeframe': 1440}
        headers = {'Accepts': 'application/json'}

        resp = requests.get(url, params=params, headers=headers)

        print(resp.content)

        return []

    def predictions(self, stop, route=None):
        return []
        # TODO: better system for this
        if stop.agency.id == 'lex:71':
            return self._lextran_predictions(route, stop)
        elif stop.agency.id == 'van:CMBC':
            return self._translink_predictions(route, stop)
        return []
