import py
import textwrap
from contextlib import contextmanager
from pypytools import compat

class Code(object):

    def __init__(self, pyx=False):
        self.pyx = pyx
        self._lines = []
        self._indentation = 0
        self._globals = compat.newdict('module')
        self.global_scope = Scope(self)
        if self.pyx:
            self.global_scope.cpdef = 'cpdef'
        else:
            self.global_scope.cpdef = 'def'
        #
        self.new_scope = self.global_scope.new_scope
        self.w = self.global_scope.w
        self.ww = self.global_scope.ww
        self.block = self.global_scope.block
        self.def_ = self.global_scope.def_
        self.cpdef_ = self.global_scope.cpdef_

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


class Scope(object):

    # use __slots__ to ensure that we can have a __code attribute without
    # having it in __dict__: we want __dict__ to be empty by default, so that
    # we know when to apply formatting
    __slots__ = ['__code', '__dict__']

    def __init__(self, code, **kwargs):
        self.__code = code
        self.__dict__.update(kwargs)

    def _kwargs(self, kwargs):
        if self.__dict__:
            d = self.__dict__.copy()
            d.update(kwargs)
            return d
        return kwargs

    def new_scope(self, **kwargs):
        kwargs = self._kwargs(kwargs)
        return Scope(self.__code, **kwargs)

    def format(self, s, **kwargs):
        kwargs = self._kwargs(kwargs)
        if kwargs:
            s = s.format(**kwargs)
        return s

    def w(self, *parts, **kwargs):
        s = ' '.join(parts)
        s = self.format(s, **kwargs)
        self.__code._lines.append(' ' * self.__code._indentation + s)

    def ww(self, s, **kwargs):
        """
        Like code.w, but dedent the code first. Useful with triple-quoted strings
        """
        s = textwrap.dedent(s[1:])
        for line in s.splitlines():
            self.w(line, **kwargs)

    @contextmanager
    def block(self, s=None, autopass=True, **kwargs):
        ns = self.new_scope(**kwargs)
        if s is not None:
            ns.w(s)
        self.__code._indentation += 4
        n = len(self.__code._lines)
        yield ns
        if autopass and n == len(self.__code._lines):
            # we didn't write anything in the block, so automatically put a 'pass'
            ns.w('pass')
        self.__code._indentation -= 4

    def def_(self, funcname, varnames, args=None, kwargs=None):
        arglist = Code.args(varnames, args, kwargs)
        return self.block('def {funcname}({arglist}):',
                          funcname=funcname, arglist=arglist)

    def cpdef_(self, funcname, varnames, args=None, kwargs=None):
        arglist = Code.args(varnames, args, kwargs)
        return self.block('{cpdef} {funcname}({arglist}):',
                          funcname=funcname, arglist=arglist)
