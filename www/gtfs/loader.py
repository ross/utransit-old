#
#
#

from collections import namedtuple
from csv import reader
from os.path import join
from pprint import pprint


class _NamedTupleReader:

    def __init__(self, name, filename, target, row_preprocessor=None):
        self.name = name
        self.filename = filename
        self.target = target
        self.row_preprocessor = row_preprocessor

        self._fieldnames = None
        self._tupleclass = None
        self._reader = reader(open(filename, 'r'))

    def __iter__(self):
        return self

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            try:
                self._fieldnames = next(self._reader)
                self.tupleclass = namedtuple(self.name, self._fieldnames)
            except StopIteration:
                pass
        return self._fieldnames

    def __next__(self):
        if self._reader.line_num == 0:
            # Used only for its side effect.
            self.fieldnames
        row = next(self._reader)
        if self.row_preprocessor:
            row = self.row_preprocessor(row, self.fieldnames)

        ret = self.tupleclass(*row)
        self.target.append(ret)
        return ret


def _trim_row(row, fieldnames):
    return [col.lstrip().rstrip() for col in row]


class GTFSLoader:

    def __init__(self, dir):
        self.dir = dir

        self._agencies = None
        self._routes = None
        self._trips = None
        self._stop_times = None
        self._stops = None
        self._shapes = None
        self._calendar = None
        self._calendar_dates = None

    @property
    def agencies(self):
        if self._agencies:
            return self._agencies
        self._agencies = []
        return _NamedTupleReader('Agency', join(self.dir, 'agency.txt'),
                                 target=self._agencies)

    @property
    def routes(self):
        if self._routes:
            return self._routes
        self._routes = []
        return _NamedTupleReader('Route', join(self.dir, 'routes.txt'),
                                 target=self._routes,
                                 row_preprocessor=_trim_row)

    @property
    def trips(self):
        if self._trips:
            return self._trips
        self._trips = []
        return _NamedTupleReader('Trip', join(self.dir, 'trips.txt'),
                                 target=self._trips,
                                 row_preprocessor=_trim_row)

    @property
    def stop_times(self):
        if self._stop_times:
            return self._stop_times
        self._stop_times = []
        return _NamedTupleReader('StopTime', join(self.dir, 'stop_times.txt'),
                                 target=self._stop_times)

    @property
    def stops(self):
        if self._stops:
            return self._stops
        self._stops = []
        return _NamedTupleReader('Stop', join(self.dir, 'stops.txt'),
                                 target=self._stops,
                                 row_preprocessor=_trim_row)

    @property
    def shapes(self):
        if self._shapes:
            return self._shapes
        self._shapes = []
        return _NamedTupleReader('Shape', join(self.dir, 'shapes.txt'),
                                 target=self._shapes)

    @property
    def calendar(self):
        if self._calendar:
            return self._calendar
        self._calendar = []
        return _NamedTupleReader('Calendar', join(self.dir, 'calendar.txt'),
                                 target=self._calendar)

    @property
    def calendar_dates(self):
        if self._calendar_dates:
            return self._calendar_dates
        self._calendar_dates = []
        return _NamedTupleReader('CalendarDate',
                                 join(self.dir, 'calendar_dates.txt'),
                                 target=self._calendar_dates)
