class PyPyLog(object):

    def __init__(self):
        self._events = []

    def add(self, section, start, end):
        self._events.append((section, start, end))

    def all_events(self):
        return self._events

