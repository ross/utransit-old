#
#
#

from collections import namedtuple
from csv import reader
from os.path import join
from pprint import pprint


class _NamedTupleReader:

    def __init__(self, name, filename, row_preprocessor=None):
        self.name = name
        self.filename = filename
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

        return self.tupleclass(*row)


def _trim_row(row, fieldnames):
    return [col.lstrip().rstrip() for col in row]


class GTFSLoader:

    def __init__(self, dir):
        self.dir = dir

    @property
    def agencies(self):
        return _NamedTupleReader('Agency', join(self.dir, 'agency.txt'))

    @property
    def routes(self):
        return _NamedTupleReader('Route', join(self.dir, 'routes.txt'),
                                 _trim_row)

    @property
    def trips(self):
        return _NamedTupleReader('Trip', join(self.dir, 'trips.txt'))

    @property
    def stop_times(self):
        return _NamedTupleReader('StopTime', join(self.dir, 'stop_times.txt'))

    @property
    def stops(self):
        return _NamedTupleReader('Stop', join(self.dir, 'stops.txt'),
                                 _trim_row)

    @property
    def shapes(self):
        return _NamedTupleReader('Shape', join(self.dir, 'shapes.txt'))

    @property
    def calendar(self):
        return _NamedTupleReader('Calendar', join(self.dir, 'calendar.txt'))

    @property
    def calendar_dates(self):
        return _NamedTupleReader('CalendarDate',
                                 join(self.dir, 'calendar_dates.txt'))
