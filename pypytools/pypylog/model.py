import itertools
from collections import defaultdict
import attr
import numpy as np

@attr.s
class Event(object):
    section = attr.ib()
    start = attr.ib()
    end = attr.ib()
    depth = attr.ib()


class PyPyLog(object):

    def __init__(self):
        self._events = []

    def add_event(self, ev):
        self._events.append(ev)

    def all_events(self):
        return self._events


class GroupedPyPyLog(object):

    def __init__(self):
        self.sections = defaultdict(list)

    def add_event(self, ev):
        self.sections[ev.section].append(ev)


class Series(object):

    def __init__(self, n, dtype='f'):
        self.X = np.empty(n, dtype=dtype)
        self.Y = np.empty(n, dtype=dtype)

    @classmethod
    def from_points(cls, points):
        res = cls(len(points))
        for i, (x, y) in enumerate(points):
            res.X[i] = x
            res.Y[i] = y
        return res

    def __len__(self):
        assert len(self.X) == len(self.Y)
        return len(self.X)

    def __iter__(self):
        for x, y in itertools.izip(self.X, self.Y):
            yield x, y

    def __getitem__(self, i):
        return self.X[i], self.Y[i]

    def __setitem__(self, i, p):
        x, y = p
        self.X[i] = x
        self.Y[i] = y

def make_step_chart(events):
    """
    Construct a Series which appears like a step chart when you draw it using
    connect='pairs'
    """
    # for each event we draw three lines, i.e. 6 points
    n = len(events)
    s = Series(n*6)
    i = 0
    for ev in events:
        h = ev.end - ev.start
        s[i+0] = (ev.start, 0)
        s[i+1] = (ev.start, h)
        #
        s[i+2] = (ev.start, h)
        s[i+3] = (ev.end, h)
        #
        s[i+4] = (ev.end, h)
        s[i+5] = (ev.end, 0)
        #
        i += 6
    #
    return s
