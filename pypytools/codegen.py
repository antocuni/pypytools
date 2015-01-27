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

    def w(self, *parts, **kwargs):
        s = ' '.join(parts)
        if kwargs:
            s = s.format(**kwargs)
        self._lines.append(' ' * self._indentation + s)

    @contextmanager
    def block(self, s=None, **kwargs):
        if s is not None:
            self.w(s, **kwargs)
        self._indentation += 4
        yield
        self._indentation -= 4

    @staticmethod
    def args(varnames, args=None, kwargs=None):
        varnames = list(varnames)
        if args is not None:
            varnames.append(args)
        if kwargs is not None:
            varnames.append(kwargs)
        return ', '.join(varnames)

    @staticmethod
    def call(funcname, varnames, args=None, kwargs=None):
        arglist = Code.args(varnames, args, kwargs)
        return '{funcname}({arglist})'.format(funcname=funcname,
                                              arglist=arglist)

    def def_(self, funcname, varnames, args=None, kwargs=None):
        arglist = self.args(varnames, args, kwargs)
        return self.block('def {funcname}({arglist}):',
                          funcname=funcname, arglist=arglist)
