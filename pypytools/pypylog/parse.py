import re
from pypytools.pypylog import model

# stolen from rpython/tool/logparse.py
_color = "(?:\x1b.*?m)?"
RE_START = re.compile(_color + r"\[([0-9a-fA-F]+)\] \{([\w-]+)" + _color + "$")
RE_STOP  = re.compile(_color + r"\[([0-9a-fA-F]+)\] ([\w-]+)\}" + _color + "$")

class ParseError(Exception):
    pass


class BaseParser(object):

    def __init__(self, freq):
        self.freq = freq

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
                return None, None, None
        #
        timestamp = m.group(1)
        name = m.group(2)
        return kind, self.parse_timestamp(timestamp), name

    def parse_timestamp(self, ts):
        return int(ts, 16) / self.freq

    def feed(self, f):
        for line in f:
            if line == '\n':
                continue
            kind, ts, name = self.parse_line(line)
            if kind == 'start':
                self.start(ts, name)
            elif kind == 'stop':
                self.stop(ts, name)
            elif kind is None:
                self.line(line)
            else:
                assert False

    def start(self, ts, name):
        pass

    def stop(self, ts, name):
        pass

    def line(self, line):
        pass


class FlatParser(BaseParser):

    def __init__(self, log, freq=1):
        BaseParser.__init__(self, freq)
        self.stack = []
        self.log = log
        self.zero_ts = None

    def start(self, ts, name):
        if self.zero_ts is None:
            self.zero_ts = ts
        self.stack.append((ts, name))

    def stop(self, ts, name):
        start_ts, start_name = self.stack.pop()
        if start_name != name:
            msg = "End section does not match start: expected %s, got %s"
            raise ParseError(msg % (start_name, name))
        depth = len(self.stack)
        ev = model.Event(name, start_ts-self.zero_ts, ts-self.zero_ts, depth)
        self.log.add_event(ev)


def flat(fname, log=None, freq=1):
    def parse_file(f):
        p = FlatParser(log, freq)
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
