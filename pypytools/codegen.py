import py
from contextlib import contextmanager
from pypytools import compat

class Code(object):

    def __init__(self):
        self._lines = []
        self._indentation = 0
        self._globals = compat.newdict('module')
        self.kwargs = {}

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

    def new_global(self, name, value):
        if name in self._globals:
            ext_value = self._globals[name]
            if value == ext_value:
                return name # nothing to do
            else:
                # try to find an unique name
                name = self._new_global_name(name)
        self._globals[name] = value
        return name

    def _new_global_name(self, name):
        i = 1
        while True:
            tryname = '%s__%d' % (name, i)
            if tryname not in self._globals:
                return tryname
            i += 1

    def w(self, *parts, **kwargs):
        s = ' '.join(parts)
        if self.kwargs or kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
            s = s.format(**kw)
        self._lines.append(' ' * self._indentation + s)

    @contextmanager
    def block(self, s=None, **kwargs):
        with self.vars(**kwargs):
            if s is not None:
                self.w(s)
            self._indentation += 4
            yield
            self._indentation -= 4

    @contextmanager
    def vars(self, **kwargs):
        original_kwargs = self.kwargs.copy()
        self.kwargs.update(kwargs)
        yield
        self.kwargs = original_kwargs

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
