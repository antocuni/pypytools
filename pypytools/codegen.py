import py
from contextlib import contextmanager

class Code(object):

    def __init__(self):
        self._lines = []
        self._indentation = 0
        self._globals = {}

    def build(self):
        return '\n'.join(self._lines)

    def compile(self):
        src = self.build()
        src = py.code.Source(src)
        co = src.compile()
        exec co in self._globals

    def __getitem__(self, name):
        return self._globals[name]

    def __setitem__(self, name, value):
        self._globals[name] = value

    def w(self, s):
        self._lines.append(' ' * self._indentation + s)

    @contextmanager
    def block(self, s=None):
        if s is not None:
            self.w(s)
        self._indentation += 4
        yield
        self._indentation -= 4
