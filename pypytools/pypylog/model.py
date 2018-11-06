import itertools
from collections import defaultdict
import attr
import numpy as np

@attr.s
class Event(object):
    tsid = attr.ib() # unique identifier for an event
    section = attr.ib()
    start = attr.ib()
    end = attr.ib()

    def as_point(self):
        x = self.start
        y = self.end - self.start
        return x, y

@attr.s
class GcMinor(Event):
    memory = attr.ib(default=None)

@attr.s
class GcCollectStep(Event):
    phase = attr.ib(default=None)


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

    def print_summary(self):
        fmt = '%-28s %6s %8s'
        print fmt % ('section', 'n', 'delta')
        print '-'*44
        for name, events in sorted(self.sections.iteritems()):
            total = 0
            for ev in events:
                delta = ev.end - ev.start
                assert delta >= 0
                total += delta
            print fmt % (name, len(events), format(delta, '.4f'))

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

    @classmethod
    def from_events(cls, events):
        return cls.from_points([ev.as_point() for ev in events])

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
        _, h = ev.as_point()
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
