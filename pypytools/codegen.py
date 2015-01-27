from contextlib import contextmanager

class Code(object):

    def __init__(self):
        self._lines = []
        self._indentation = 0

    def build(self):
        return '\n'.join(self._lines)

    def w(self, s):
        self._lines.append(' ' * self._indentation + s)

    @contextmanager
    def block(self, s=None):
        if s is not None:
            self.w(s)
        self._indentation += 4
        yield
        self._indentation -= 4
