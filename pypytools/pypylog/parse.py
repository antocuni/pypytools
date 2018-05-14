import re
import attr
from pypytools.pypylog import model

# stolen from rpython/tool/logparse.py
_color = "(?:\x1b.*?m)?"
RE_START = re.compile(_color + r"\[([0-9a-fA-F]+)\] \{([\w-]+)" + _color + "$")
RE_STOP  = re.compile(_color + r"\[([0-9a-fA-F]+)\] ([\w-]+)\}" + _color + "$")

class ParseError(Exception):
    pass


@attr.s
class Section(object):
    tsid = attr.ib()
    name = attr.ib()
    start = attr.ib()
    stop = attr.ib(default=None)
    lines = attr.ib(default=attr.Factory(list))

class BaseParser(object):
    COLLECT_LINES = None

    def __init__(self, log, freq):
        self.log = log
        self.freq = freq

    @classmethod
    def from_file(cls, fname, log=None, freq=1):
        def parse_file(f):
            p = cls(log, freq)
            p.feed(f)
            return log
        #
        if log is None:
            log = model.PyPyLog()
        if isinstance(fname, basestring):
            with open(fname) as f:
                return parse_file(f)
        else:
            return parse_file(fname)

    def parse_line(self, line):
        m = RE_START.match(line)
        if m:
            kind = 'start'
        else:
            m = RE_STOP.match(line)
            if m:
                kind = 'stop'
            else:
                # no start or stop
                return None, None, None, None
        #
        timestamp = m.group(1)
        name = m.group(2)
        return kind, timestamp, self.parse_timestamp(timestamp), name

    def parse_timestamp(self, ts):
        return int(ts, 16) / self.freq

    def feed(self, f):
        zero_ts = None
        stack = []
        for line in f:
            if line == '\n':
                continue
            kind, tsid, ts, name = self.parse_line(line)
            if zero_ts is None:
                zero_ts = ts
            if kind == 'start':
                stack.append(Section(tsid, name, start=ts-zero_ts))
            elif kind == 'stop':
                if name != stack[-1].name:
                    msg = "End section does not match start: expected %s, got %s"
                    raise ParseError(msg % (stack[-1].name, name))
                stack[-1].stop = ts - zero_ts
                self.section(stack[-1])
                stack.pop()
            elif kind is None:
                if self.COLLECT_LINES:
                    stack[-1].lines.append(line)
            else:
                assert False

    def section(self, s):
        pass


class FlatParser(BaseParser):

    def __init__(self, log, freq=1):
        BaseParser.__init__(self, log, freq)

    def section(self, s):
        ev = model.Event(s.tsid, s.name, s.start, s.stop)
        self.log.add_event(ev)


class GcParser(FlatParser):
    COLLECT_LINES = True
    RE_MINOR = re.compile('minor collect, total memory used: ([0-9]*)')
    RE_STEP = re.compile('starting gc state: (.*)')

    def section(self, s):
        name = 'on_%s' % (s.name.replace('-', '_'))
        meth = getattr(self, name, None)
        if meth:
            meth(s)
        else:
            FlatParser.section(self, s)

    def _scan_for_regex(self, regex, lines):
        for line in lines:
            m = regex.match(line)
            if m:
                return m.group(1).strip()
        return None

    def on_gc_minor(self, s):
        memory = self._scan_for_regex(self.RE_MINOR, s.lines)
        if memory:
            memory = int(memory)
        ev = model.GcMinor(s.tsid, s.name, s.start, s.stop, memory=memory)
        self.log.add_event(ev)

    def on_gc_collect_step(self, s):
        phase = self._scan_for_regex(self.RE_STEP, s.lines)
        ev = model.GcCollectStep(s.tsid, s.name, s.start, s.stop, phase=phase)
        self.log.add_event(ev)


flat = FlatParser.from_file
gc = GcParser.from_file

def parse_frequency(s):
    """
    Parse an human-readable string and return the frequency expressed in
    hertz.  It supports different units such as Hz, hz, MHz, GHz, etc.
    """
    s = s.lower().strip()
    if s.endswith('hz'):
        s = s[:-2]
    if not s:
        raise ValueError
    unit = s[-1]
    factor = 1
    if unit == 'k':
        factor = 10**3
    elif unit == 'm':
        factor = 10**6
    elif unit == 'g':
        factor = 10**9
    if factor != 1:
        s = s[:-1]
    return float(s) * factor
